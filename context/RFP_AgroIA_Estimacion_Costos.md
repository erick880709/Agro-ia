> Solicitud de propuesta · AgroIA v4 · Módulo AGC-COST

# Estimación de costos de trabajos con parámetros administrables

AgroIA necesita cotizar el trabajo de campo —muestreo en grilla, visitas técnicas, instalación de sensores— con un motor de cálculo que el administrador configure desde la propia aplicación. Ningún valor monetario, tramo, recargo ni regla de densidad puede quedar escrito en el código.

```
Comisión_visita = Tarifa_base + (Puntos × Tarifa_por_punto_escalonada) + Recargo_dificultad
```

Fórmula de referencia del estudio de tarifas. El módulo debe reproducirla exactamente y, además, permitir extenderla sin desplegar código nuevo.

**Proyecto:** AGROINTELIGENTE COLOMBIA · **Producto:** AgroIA (SPA + FastAPI + PostgreSQL) · **Versión del documento:** 1.0 · **Fecha:** 18 de septiembre de 2026 · **Moneda:** COP

## 1. Resumen ejecutivo

AgroIA ya administra fincas, lotes, comisiones de toma de medidas, equipo de trabajo con tarifas por rol, insumos y precios de cosecha. Lo que falta es el eslabón previo a la comisión: **cuánto cuesta y cuánto se cobra el trabajo antes de comprometerlo**. Hoy esa cifra se calcula fuera del sistema, en hojas de cálculo y conversaciones, y no queda trazable ni reproducible.

Se solicita construir **AGC-COST**, un módulo con tres piezas: un **catálogo de parámetros versionado** que administra el rol Administrador, un **motor de cálculo determinista** que resuelve la fórmula a partir de esos parámetros, y un **cotizador** que produce estimaciones desglosadas, auditables y convertibles en comisión.

El criterio de éxito no es que el número salga: es que el número salga **explicado, reproducible y modificable sin tocar el repositorio**. Un cambio de tarifa base o de recargo por pendiente debe ser una operación de negocio de dos minutos, no un despliegue.

## 2. Contexto y problema

El estudio de tarifas de muestreo en grilla dejó cuatro hallazgos que condicionan el diseño:

- El costo de desplazamiento y montaje del técnico es **prácticamente fijo**, sin importar si el lote tiene 1 o 50 hectáreas. Ese costo se diluye a medida que crece el área.
- El costo por hectárea cae de **$250.000 a $10.200 COP** entre el lote más pequeño y el más grande del ejercicio: una diferencia de 24 veces. Esto es comportamiento correcto del modelo, no un error, y el sistema debe mostrarlo sin alarmar al usuario.
- La densidad de puntos no es lineal con el área: entre 8 y 15 puntos en lotes pequeños, ~1 punto/ha en lotes medianos, ~0,7 puntos/ha en fincas grandes.
- Las cifras del ejercicio son **ilustrativas**: no existe tarifa pública colombiana confirmada para este servicio. El sistema debe tratarlas como datos iniciales sustituibles, nunca como constantes.

> **Riesgo que el módulo debe cubrir explícitamente:** el total absoluto en pesos de un lote pequeño puede quedar por debajo del costo real del viaje aunque el costo por hectárea se vea alto. El motor debe vigilar el piso de rentabilidad en pesos, no el indicador por hectárea.

## 3. Objetivos y alcance

### Objetivos

1.  Estimar el costo y el precio de venta de un trabajo de campo desde la ficha de la finca o del lote, en menos de un minuto.
2.  Permitir que el Administrador cree, edite, simule, apruebe y publique conjuntos de parámetros sin intervención de desarrollo.
3.  Garantizar que cada estimación emitida sea reproducible dígito a dígito años después, aunque los parámetros hayan cambiado.
4.  Conectar la estimación aceptada con el flujo existente de comisiones y lista de trabajos.

### Dentro del alcance

- Catálogo de servicios cotizables y sus componentes de costo.
- Motor de cálculo declarativo, versionado y auditado.
- Pantalla de administración de parámetros con simulador.
- Cotizador con desglose, márgenes, descuentos, impuestos informativos y exportación a PDF/HTML.
- **Cotización en PDF con la identidad de la empresa**: logo de AgroIA, sitio web, teléfonos de contacto y datos legales, todos administrados como parámetros.
- **Conversión de la cotización aceptada en documento de cobro** (cuenta de cobro o factura), con numeración consecutiva controlada y seguimiento de pago.
- Ciclo de vida de la estimación: borrador → emitida → aceptada/rechazada/vencida → convertida en comisión y en documento de cobro.
- Migración de los valores del estudio como conjunto de parámetros semilla.

### Fuera del alcance de esta contratación

- **Validación previa ante la DIAN** (XML UBL 2.1, CUFE, proveedor tecnológico autorizado). El módulo genera el documento de cobro y deja preparada la integración; la habilitación DIAN se contrata aparte. Ver sección 17.
- Pasarela de pagos y conciliación bancaria automática.
- Nómina y liquidación real del equipo de campo (el módulo consume tarifas, no las liquida).
- Firma electrónica certificada de la cotización.
- Optimización de rutas de visita.

## 4. Glosario

| Término                    | Definición operativa                                                                                                                                   |
|----------------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------|
| **Servicio**               | Trabajo cotizable del catálogo: muestreo en grilla, muestreo simple, análisis de agua, instalación de sensor, visita de diagnóstico, capacitación BPA. |
| **Componente**             | Sumando del costo: tarifa base, tramos por punto, desplazamiento, laboratorio, mano de obra, insumos.                                                  |
| **Factor**                 | Ajuste porcentual o multiplicativo: dificultad del terreno, zona, urgencia, día no hábil.                                                              |
| **Conjunto de parámetros** | Fotografía completa y versionada de todos los componentes, tramos, factores y políticas, con fecha de vigencia.                                        |
| **Estimación**             | Cálculo persistido para una finca/lote con su desglose y el conjunto de parámetros congelado.                                                          |
| **Piso de rentabilidad**   | Valor mínimo en pesos por debajo del cual una visita no se emite sin autorización expresa.                                                             |
| **Snapshot**               | Copia inmutable de los parámetros resueltos que se guarda dentro de la estimación emitida.                                                             |

## 5. Arquitectura funcional

Tres capas con responsabilidades separadas. La regla dura de diseño: **la capa de cálculo no conoce ningún valor de negocio**; solo sabe interpretar componentes y factores que le entrega la capa de parámetros.

    ┌──────────────────────────────────────────────────────────────┐
    │  1. CATÁLOGO DE PARÁMETROS  (Admin · versionado · aprobado)   │
    │     servicios · componentes · tramos · factores · zonas       │
    │     laboratorio · impuestos · política comercial · vigencias  │
    └───────────────────────────┬──────────────────────────────────┘
                                │ resuelve conjunto vigente a fecha
    ┌───────────────────────────▼──────────────────────────────────┐
    │  2. MOTOR DE CÁLCULO  (puro · determinista · sin estado)      │
    │     entrada: contexto del lote + selecciones del usuario      │
    │     salida: líneas de desglose + totales + trazas por línea   │
    └───────────────────────────┬──────────────────────────────────┘
                                │ resultado + snapshot de parámetros
    ┌───────────────────────────▼──────────────────────────────────┐
    │  3. COTIZADOR / ESTIMACIONES  (flujo de negocio)              │
    │     borrador → emitida → aceptada → comisión → lista trabajos │
    └──────────────────────────────────────────────────────────────┘

> **Por qué esta separación importa:** permite exponer el motor como función pura testeable con los cuatro casos de aceptación de la sección 15, y permite que la PWA calcule en modo offline con el conjunto de parámetros cacheado, revalidando al sincronizar.

## 6. Dominios de parámetros administrables

Todo lo listado a continuación es dato editable en pantalla. Nada de esto se admite como constante en el código, archivo de configuración desplegado ni variable de entorno.

| Grupo                                    | Parámetros que administra                                                                                                                                                                                                                                                                                          | Por qué                                                                                                                                                                                                                   |
|------------------------------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| P-01 · Servicios                         | Código, nombre, descripción, unidad de medida (punto / hectárea / dispositivo / día / visita), activo, orden, ícono, si requiere lote o solo finca.                                                                                                                                                                | El catálogo crecerá con análisis de agua, MIP y riego previstos en la v4.                                                                                                                                                 |
| P-02 · Tarifa base                       | Valor fijo por servicio (desplazamiento + montaje), si es afectable por factores, si incluye un mínimo de puntos.                                                                                                                                                                                                  | Es el costo que se diluye con el área; debe poder ajustarse por inflación sin tocar los tramos.                                                                                                                           |
| P-03 · Tramos escalonados                | Por servicio: `desde`, `hasta`, valor unitario, tipo de escalonamiento (marginal o por tramo completo). Número de tramos ilimitado.                                                                                                                                                                                | Hoy son 1–15 / 16–30 / 31+, mañana pueden ser cinco tramos o ninguno.                                                                                                                                                     |
| P-04 · Densidad de muestreo              | Por rango de área: puntos mínimos, puntos máximos, puntos por hectárea sugeridos, redondeo. Opcionalmente por cultivo.                                                                                                                                                                                             | Automatiza la sugerencia de puntos y evita que el técnico improvise densidades no representativas.                                                                                                                        |
| P-05 · Factores de dificultad            | Escalas nombradas con opciones y porcentaje: pendiente (plano 0% / moderada 15% / alta 30%), acceso, pedregosidad, altitud. Marcar si se combinan sumando o multiplicando.                                                                                                                                         | La finca ya registra profundidad efectiva y pedregosidad: el factor puede precargarse desde el predio.                                                                                                                    |
| P-06 · Zonas y desplazamiento            | Factor por departamento/municipio, kilómetros incluidos en la base, tarifa por km excedente, peajes estimados, umbral de días para viáticos, valor de viático y pernoctación.                                                                                                                                      | Un lote en el Quindío y uno en Vichada no cuestan lo mismo aunque tengan el mismo tamaño.                                                                                                                                 |
| P-07 · Laboratorio y muestras            | Costo por muestra compuesta según paquete de análisis (completo, básico, físico-químico), puntos por muestra compuesta, costo de empaque y envío, laboratorio proveedor.                                                                                                                                           | Separa lo que se paga a un tercero de lo que gana la operación propia.                                                                                                                                                    |
| P-08 · Mano de obra                      | Rendimiento esperado en puntos por jornada por rol, número de personas del equipo, tarifa día por rol (reutiliza «Equipo de trabajo»), factor prestacional.                                                                                                                                                        | Es el insumo para calcular el costo real y compararlo contra el precio ofertado.                                                                                                                                          |
| P-09 · Insumos y equipos                 | Consumibles por punto o por visita (bolsas, etiquetas, barrenos), depreciación de equipo por jornada. Reutiliza «Administrar insumos» donde aplique.                                                                                                                                                               | Evita duplicar catálogos ya existentes en la aplicación.                                                                                                                                                                  |
| P-10 · Política comercial                | Margen objetivo, margen mínimo con alerta, piso de rentabilidad por visita, descuento máximo por rol, vigencia de la cotización en días, regla de redondeo (múltiplo y modo).                                                                                                                                      | Traduce la estrategia de precios en barandas verificables por el sistema.                                                                                                                                                 |
| P-11 · Descuentos y recargos comerciales | Por volumen de hectáreas, por número de fincas del mismo cliente, por contrato anual, por asociación o cooperativa, por urgencia y por día no hábil.                                                                                                                                                               | Comercialización a asociaciones cafeteras y alianzas productivas del proyecto.                                                                                                                                            |
| P-12 · Impuestos y retenciones           | IVA, ReteFuente, ReteICA por municipio, AIU si aplica; cada uno con base gravable y bandera de «informativo» o «incluido en el total».                                                                                                                                                                             | La cotización debe mostrar el valor que el cliente realmente paga.                                                                                                                                                        |
| P-13 · Vigencias e indexación            | Fecha de inicio y fin del conjunto, moneda, índice de reajuste (IPC / SMMLV), porcentaje de reajuste masivo con vista previa.                                                                                                                                                                                      | Un reajuste anual debe ser una acción, no una edición de 60 celdas.                                                                                                                                                       |
| P-14 · Identidad y contacto              | Logo (carga de imagen, versión clara y oscura), nombre comercial, razón social, NIT y régimen, **sitio web**, **lista de teléfonos de contacto** con etiqueta y orden, correo electrónico, dirección, ciudad, redes sociales, pie de página legal, texto de términos y condiciones, color de acento del documento. | Los datos de contacto cambian: hoy son el sitio `jeepaoaisystems.com` y el teléfono 3242013807, mañana puede haber una línea adicional o una sede nueva. Ninguno de esos valores puede vivir en una plantilla desplegada. |
| P-15 · Documentos de cobro               | Tipo de documento habilitado (cuenta de cobro / factura de venta), prefijo y rango de numeración, resolución DIAN y su vigencia, plazo de pago en días, medios de pago aceptados, cuenta bancaria para consignación, textos legales obligatorios, retenciones aplicables, moneda y notas al pie.                   | La numeración consecutiva y la resolución son datos regulados con vigencia propia: deben administrarse y auditarse, nunca inventarse en código.                                                                           |

> **Sobre el logo y los archivos de marca.** El logo se administra como archivo cargado desde la pantalla de parámetros, con validación de formato (PNG o SVG), tamaño máximo y previsualización en el documento antes de guardar. Se almacena una URL estable, no un archivo incrustado en el repositorio, para que cambiar la marca no requiera despliegue.

## 7. Requisitos funcionales

Prioridad: **DEBE** obligatorio en la primera entrega · **DEBERÍA** obligatorio antes del cierre · **PODRÍA** deseable.

| ID    | Requisito                                                                                                                                                | Criterio de aceptación                                                                                  | Prior.  |
|-------|----------------------------------------------------------------------------------------------------------------------------------------------------------|---------------------------------------------------------------------------------------------------------|---------|
| RF-01 | CRUD de servicios cotizables.                                                                                                                            | Crear un servicio nuevo y cotizarlo sin desplegar código.                                               | DEBE    |
| RF-02 | CRUD de componentes de costo por servicio, con orden de aplicación y bandera de afectable por factores.                                                  | Reordenar componentes cambia el resultado de forma coherente y queda en auditoría.                      | DEBE    |
| RF-03 | CRUD de tramos escalonados con validación de continuidad y no solapamiento.                                                                              | El sistema rechaza tramos con huecos o traslapes con mensaje que indica el rango en conflicto.          | DEBE    |
| RF-04 | CRUD de escalas de factores con opciones y porcentajes.                                                                                                  | Agregar una opción «pendiente extrema 45%» queda disponible en el cotizador de inmediato.               | DEBE    |
| RF-05 | Reglas de densidad de muestreo por rango de área.                                                                                                        | Al elegir un lote de 20 ha el cotizador propone 20 puntos y permite sobrescribirlos.                    | DEBE    |
| RF-06 | Sugerencia editable de puntos con advertencia si el usuario baja del mínimo de representatividad.                                                        | Al poner 4 puntos en 20 ha aparece advertencia no bloqueante con el motivo agronómico.                  | DEBE    |
| RF-07 | Cálculo de desplazamiento por distancia desde una sede configurable hasta las coordenadas de la finca.                                                   | Km calculados a partir de la georreferenciación ya registrada; editable manualmente.                    | DEBERÍA |
| RF-08 | Estimación multi-lote y multi-servicio en una sola cotización.                                                                                           | Una finca con 3 lotes produce una cotización con subtotales por lote y un total consolidado.            | DEBERÍA |
| RF-09 | Desglose línea por línea con el origen de cada valor.                                                                                                    | Cada línea muestra qué parámetro la produjo y con qué cantidad.                                         | DEBE    |
| RF-10 | Indicadores derivados: costo por punto, costo por hectárea, costo directo, margen en pesos y en porcentaje.                                              | Coinciden con la tabla comparativa del estudio para los cuatro casos de prueba.                         | DEBE    |
| RF-11 | Comparación costo real vs. precio ofertado y alerta si el margen cae bajo el mínimo.                                                                     | Alerta visible antes de emitir, con el valor faltante en pesos.                                         | DEBE    |
| RF-12 | Piso de rentabilidad: bloquear emisión por debajo del mínimo salvo autorización de rol superior con justificación.                                       | Intento de emitir por debajo del piso exige comentario y queda en auditoría.                            | DEBE    |
| RF-13 | Descuento comercial con tope por rol.                                                                                                                    | Un agrónomo no puede exceder su tope; el administrador sí, y queda registrado.                          | DEBERÍA |
| RF-14 | Versionado de conjuntos de parámetros con estados borrador / en revisión / publicado / archivado.                                                        | Solo un conjunto publicado vigente por fecha; publicar archiva el anterior sin borrarlo.                | DEBE    |
| RF-15 | Aprobación de doble control: quien edita no puede publicar.                                                                                              | El sistema rechaza la publicación si el aprobador es el mismo usuario que editó.                        | DEBE    |
| RF-16 | Simulador what-if sobre un conjunto en borrador, sin afectar producción.                                                                                 | Comparativa lado a lado del mismo caso con parámetros vigentes vs. borrador.                            | DEBE    |
| RF-17 | Snapshot inmutable de parámetros dentro de cada estimación emitida.                                                                                      | Recalcular una estimación de hace un año devuelve el mismo total al peso.                               | DEBE    |
| RF-18 | Clonar un conjunto y aplicar reajuste porcentual masivo con vista previa.                                                                                | Reajuste del 9% sobre todos los valores monetarios con lista de cambios antes de confirmar.             | DEBERÍA |
| RF-19 | Ciclo de vida de la estimación con vencimiento automático.                                                                                               | Al superar la vigencia configurada pasa a «vencida» y no puede aceptarse.                               | DEBERÍA |
| RF-20 | Conversión de estimación aceptada en comisión, precargando equipo, fechas y valor.                                                                       | La comisión creada referencia la estimación de origen y aparece en la lista de trabajos.                | DEBE    |
| RF-21 | Exportar la cotización en HTML y PDF con lenguaje claro para el agricultor.                                                                              | Misma lógica de audiencia que ya usan los reportes: versión simple y versión técnica.                   | DEBERÍA |
| RF-22 | Auditoría completa de cambios de parámetros y de estimaciones en la bitácora existente.                                                                  | Valor anterior, valor nuevo, usuario, fecha y motivo consultables y filtrables.                         | DEBE    |
| RF-23 | Importar y exportar conjuntos de parámetros en CSV/JSON.                                                                                                 | Exportar, editar fuera de línea, reimportar con validación previa y reporte de errores.                 | PODRÍA  |
| RF-24 | Cálculo offline en la PWA con el conjunto vigente cacheado.                                                                                              | Estimación en campo sin señal; al sincronizar se revalida contra el conjunto vigente y avisa si cambió. | PODRÍA  |
| RF-25 | Tablero de estimaciones: emitidas, aceptadas, tasa de conversión y ticket promedio por servicio.                                                         | Filtros por periodo, municipio y servicio.                                                              | PODRÍA  |
| RF-26 | Generar la cotización en PDF con el logo de AgroIA, sitio web y teléfonos tomados de los parámetros de identidad.                                        | Cambiar el teléfono en parámetros y regenerar el PDF refleja el valor nuevo sin desplegar código.       | DEBE    |
| RF-27 | Administrar la identidad: cargar y previsualizar el logo, y editar sitio web, correo, dirección y lista de teléfonos con etiqueta y orden.               | Agregar un segundo teléfono lo hace aparecer en el encabezado del PDF en el orden definido.             | DEBE    |
| RF-28 | PDF con estructura fija: encabezado de marca, datos del cliente y la finca, vigencia, desglose, totales, impuestos, condiciones comerciales y pie legal. | El documento cabe en la plantilla sin desbordes con 3 lotes y 5 servicios, y pagina correctamente.      | DEBE    |
| RF-29 | Convertir una estimación aceptada en documento de cobro, heredando líneas, totales e impuestos.                                                          | El documento generado referencia la estimación de origen y no permite editar los valores heredados.     | DEBE    |
| RF-30 | Numeración consecutiva por prefijo, sin huecos ni duplicados, asignada en el servidor.                                                                   | Cien emisiones concurrentes producen cien consecutivos únicos y contiguos.                              | DEBE    |
| RF-31 | Estados del documento de cobro: emitido, enviado, pagado parcialmente, pagado, vencido, anulado.                                                         | Un documento emitido nunca se borra: se anula con motivo y queda en auditoría.                          | DEBE    |
| RF-32 | Registro de pagos con fecha, valor, medio y soporte; cálculo de saldo pendiente.                                                                         | Un abono parcial deja el documento en «pagado parcialmente» con el saldo correcto.                      | DEBERÍA |
| RF-33 | Envío del PDF al cliente por correo y por WhatsApp, reutilizando el canal de notificaciones de la v4.                                                    | Queda registro del envío con fecha y destinatario.                                                      | PODRÍA  |
| RF-34 | Estructura de datos y puntos de extensión preparados para la validación DIAN posterior.                                                                  | El modelo contempla CUFE, XML y respuesta del proveedor sin requerir migración destructiva.             | DEBERÍA |

## 8. Motor de cálculo

El motor no interpreta fórmulas de texto libre. Ejecuta una **tubería declarativa de componentes ordenados**, cada uno con un tipo conocido. Esto elimina la superficie de ejecución de código arbitrario y mantiene el cálculo auditable.

### Tipos de componente admitidos

| Tipo          | Cómo calcula                                                                           |
|---------------|----------------------------------------------------------------------------------------|
| fijo          | valor constante del parámetro                                                          |
| escalonado    | recorre los tramos marginalmente sobre la cantidad de la unidad                        |
| por_unidad    | cantidad × valor unitario                                                              |
| por_distancia | max(0, km − km_incluidos) × tarifa_km, más peajes                                      |
| por_jornada   | ceil(cantidad ÷ rendimiento) × personas × tarifa_día × factor_prestacional             |
| porcentual    | porcentaje sobre la base declarada (directo, ajustado o una línea específica)          |
| condicional   | cualquiera de los anteriores, activo solo si se cumple una condición sobre el contexto |

### Orden de resolución (no negociable)

1.  Resolver el conjunto de parámetros publicado y vigente en la `fecha_referencia`.
2.  Resolver el contexto: área del lote, puntos, km, dificultad, zona, cultivo, cliente.
3.  Ejecutar componentes en su orden y obtener **subtotal directo**.
4.  Aplicar factores sobre las líneas marcadas como afectables → **subtotal ajustado**.
5.  Aplicar margen objetivo → **precio de lista**.
6.  Aplicar descuentos comerciales, validando el tope del rol.
7.  Verificar el piso de rentabilidad y el margen mínimo; marcar advertencias.
8.  Aplicar la regla de redondeo.
9.  Calcular impuestos y retenciones (informativos o incluidos según parámetro).
10. Calcular indicadores derivados y emitir la traza completa.

> **Reglas de precisión.** Toda la aritmética monetaria usa decimal de precisión fija —`NUMERIC(18,4)` en base y `Decimal` en Python—, nunca coma flotante. El redondeo ocurre una sola vez, en el paso 8, con modo y múltiplo parametrizados. Las diferencias por redondeo se muestran como una línea explícita, no se absorben en silencio.

## 9. Modelo de datos propuesto

Propuesta de referencia; el proveedor puede mejorarla justificando los cambios. Todas las tablas llevan campos de auditoría (`creado_por`, `creado_en`, `actualizado_por`, `actualizado_en`).

    costeo_conjunto          (id, nombre, version, estado, vigencia_desde, vigencia_hasta,
                              moneda, creado_por, aprobado_por, aprobado_en, notas)
    costeo_servicio          (id, conjunto_id, codigo, nombre, unidad, requiere_lote, activo, orden)
    costeo_componente        (id, servicio_id, codigo, nombre, tipo, orden, afectable_por_factores,
                              config JSONB)
    costeo_tramo             (id, componente_id, desde, hasta, valor, modo)
    costeo_factor            (id, conjunto_id, codigo, nombre, aplicacion, combinacion)
    costeo_factor_opcion     (id, factor_id, codigo, etiqueta, porcentaje, orden)
    costeo_densidad          (id, conjunto_id, area_min, area_max, puntos_min, puntos_max,
                              puntos_por_ha, cultivo_id NULL)
    costeo_zona              (id, conjunto_id, departamento, municipio NULL, factor,
                              km_incluidos, tarifa_km, peajes_estimados)
    costeo_impuesto          (id, conjunto_id, codigo, nombre, porcentaje, base, informativo)
    costeo_politica          (id, conjunto_id, margen_objetivo, margen_minimo, piso_visita,
                              vigencia_cotizacion_dias, redondeo_multiplo, redondeo_modo)
    costeo_descuento         (id, conjunto_id, codigo, criterio, umbral, porcentaje, tope_rol JSONB)

    estimacion               (id, consecutivo, finca_id, cliente_id, estado, fecha_referencia,
                              conjunto_id, total_directo, total_ajustado, total_final,
                              margen_pct, vence_en, creado_por, emitido_por, motivo_excepcion)
    estimacion_linea         (id, estimacion_id, lote_id NULL, servicio_id, componente_codigo,
                              descripcion, cantidad, unidad, valor_unitario, valor,
                              parametro_ref JSONB)
    estimacion_snapshot      (estimacion_id, parametros JSONB, hash_sha256)
    estimacion_evento        (id, estimacion_id, evento, usuario_id, fecha, comentario)

    costeo_identidad         (id, conjunto_id, nombre_comercial, razon_social, nit, regimen,
                              sitio_web, correo, direccion, ciudad, logo_url, logo_oscuro_url,
                              color_acento, pie_legal, terminos_condiciones)
    costeo_telefono          (id, identidad_id, etiqueta, numero, whatsapp, orden)
    cobro_config             (id, conjunto_id, tipo_documento, prefijo, numero_desde, numero_hasta,
                              resolucion_dian, resolucion_vigencia_hasta, plazo_pago_dias,
                              medios_pago JSONB, cuenta_bancaria, textos_legales JSONB)
    cobro_documento          (id, consecutivo, prefijo, tipo, estimacion_id, cliente_id, estado,
                              fecha_emision, fecha_vencimiento, subtotal, impuestos, total,
                              saldo, identidad_snapshot JSONB, cufe NULL, xml_url NULL,
                              anulado_por NULL, motivo_anulacion NULL)
    cobro_linea              (id, documento_id, descripcion, cantidad, unidad, valor_unitario,
                              valor, impuesto_codigo)
    cobro_pago               (id, documento_id, fecha, valor, medio, referencia, soporte_url,
                              registrado_por)
    cobro_evento             (id, documento_id, evento, usuario_id, fecha, comentario)

El campo `identidad_snapshot` cumple en el documento de cobro el mismo papel que el snapshot de parámetros en la estimación: si la empresa cambia de teléfono o de logo, la factura emitida el año pasado se sigue reimprimiendo con los datos que tenía ese día.

La tabla `estimacion_snapshot` es el corazón de la reproducibilidad: guarda los parámetros resueltos y su hash. Recalcular con el snapshot debe producir exactamente el mismo total; cualquier diferencia es un defecto bloqueante.

## 10. Contrato de API

Sobre el prefijo existente `/api/v1`, autenticación JWT vigente, errores con el mismo formato de código de negocio que ya usa la plataforma.

| Método y ruta                                                                 | Propósito                                                  | Rol                         |
|-------------------------------------------------------------------------------|------------------------------------------------------------|-----------------------------|
| GET /costeo/conjuntos                                                         | Listar conjuntos con estado y vigencia.                    | Admin                       |
| POST /costeo/conjuntos                                                        | Crear conjunto en borrador.                                | Admin                       |
| POST /costeo/conjuntos/{id}/clonar                                            | Clonar con reajuste opcional.                              | Admin                       |
| POST /costeo/conjuntos/{id}/validar                                           | Validación integral previa a publicar.                     | Admin                       |
| POST /costeo/conjuntos/{id}/publicar                                          | Publicar con doble control.                                | Admin aprobador             |
| GET /costeo/parametros/vigentes                                               | Conjunto vigente para el cotizador y la caché PWA.         | Admin · Agrónomo            |
| POST /costeo/simular                                                          | Cálculo sin persistir, contra un conjunto indicado.        | Admin · Agrónomo            |
| POST /estimaciones                                                            | Crear estimación en borrador.                              | Admin · Agrónomo            |
| PATCH /estimaciones/{id}                                                      | Editar cantidades, factores y descuentos.                  | Admin · Agrónomo            |
| POST /estimaciones/{id}/emitir                                                | Congelar snapshot y emitir.                                | Admin · Agrónomo            |
| POST /estimaciones/{id}/aceptar                                               | Registrar aceptación del cliente.                          | Admin · Agrónomo            |
| POST /estimaciones/{id}/convertir-comision                                    | Crear la comisión asociada.                                | Admin                       |
| GET /estimaciones/{id}/export?formato=pdf\|html&audiencia=agricultor\|tecnico | Descargar la cotización con la identidad vigente.          | Todos según finca permitida |
| GET /costeo/identidad                                                         | Identidad y contactos vigentes para encabezados y PDF.     | Autenticado                 |
| PUT /costeo/identidad                                                         | Actualizar datos de identidad y lista de teléfonos.        | Admin                       |
| POST /costeo/identidad/logo                                                   | Cargar el logo con validación de formato y tamaño.         | Admin                       |
| POST /cobros                                                                  | Crear el documento de cobro desde una estimación aceptada. | Admin                       |
| POST /cobros/{id}/emitir                                                      | Asignar consecutivo, congelar identidad y emitir.          | Admin                       |
| POST /cobros/{id}/pagos                                                       | Registrar un pago total o parcial.                         | Admin                       |
| POST /cobros/{id}/anular                                                      | Anular con motivo obligatorio.                             | Admin                       |
| GET /cobros/{id}/pdf                                                          | Descargar el documento de cobro.                           | Admin · Cliente propietario |

Códigos de negocio esperados: `CONJUNTO_SIN_VIGENCIA`, `TRAMOS_INCONSISTENTES`, `APROBADOR_ES_EDITOR`, `DESCUENTO_EXCEDE_TOPE`, `BAJO_PISO_RENTABILIDAD`, `ESTIMACION_VENCIDA`, `SNAPSHOT_INCONSISTENTE`, `NUMERACION_AGOTADA`, `RESOLUCION_VENCIDA`, `COBRO_YA_EMITIDO`, `ESTIMACION_NO_ACEPTADA`.

## 11. Pantallas y UX

### Administración → Parámetros de costeo

Nueva entrada en el submenú de Administración, junto a Insumos y Precios de cosecha. Encabezado permanente con el conjunto que se está editando, su estado y su vigencia, para que nadie edite producción creyendo que edita un borrador.

- **Servicios** — Catálogo cotizable con unidad de medida y activación.

- **Tarifas y tramos** — Tarifa base y tabla de tramos editable, con vista del escalonado resultante.

- **Factores** — Escalas de dificultad, urgencia y día no hábil con sus porcentajes.

- **Zonas y desplazamiento** — Factor por municipio, km incluidos, tarifa por km y viáticos.

- **Densidad de muestreo** — Rangos de área con puntos mínimos, máximos y por hectárea.

- **Laboratorio e insumos** — Costo por muestra compuesta y consumibles por punto o visita.

- **Política comercial** — Márgenes, piso de rentabilidad, topes de descuento y redondeo.

- **Impuestos** — IVA y retenciones con base gravable y tratamiento informativo.

- **Identidad y contacto** — Logo con previsualización, sitio web, correo, dirección y teléfonos ordenables.

- **Documentos de cobro** — Tipo, prefijo, numeración, resolución, plazo de pago y textos legales.

- **Versiones y vigencias** — Historial, clonación, reajuste masivo, publicación y archivo.

- **Simulador** — Caso de prueba lado a lado: parámetros vigentes contra el borrador.

### Nueva pestaña: Estimación de costos

Visible para Administrador y Agrónomo. Flujo de cuatro pasos en una sola pantalla, con el total recalculándose en vivo a la derecha:

1.  **Finca y lotes.** Trae área, coordenadas, pedregosidad y profundidad ya registradas.
2.  **Servicios y cantidades.** Puntos sugeridos por la regla de densidad, editables, con advertencia de representatividad.
3.  **Condiciones.** Pendiente, acceso, urgencia, día no hábil, kilómetros; precargados desde la ficha del predio cuando existe el dato.
4.  **Resumen y emisión.** Desglose línea a línea, costo por punto y por hectárea, margen, descuento, advertencias, y botones «Guardar borrador» y «Emitir cotización».

Puntos de entrada adicionales: botón «Estimar» en la ficha de cada finca, en Lista de trabajos y en la creación de una comisión.

> **Cómo se comunica el costo por hectárea.** En lotes pequeños el indicador se dispara y parece un error. Junto al valor debe ir una explicación en lenguaje llano: el viaje y el montaje cuestan casi lo mismo en un lote de 1 ha que en uno de 50, así que en el lote pequeño ese costo se reparte entre menos hectáreas.

## 12. Roles y permisos

| Rol           | Parámetros e identidad                                                                                     | Estimaciones                                                   | Documentos de cobro                               |
|---------------|------------------------------------------------------------------------------------------------------------|----------------------------------------------------------------|---------------------------------------------------|
| Administrador | Crear, editar, simular, publicar (si no es el editor), archivar; administrar logo, contactos y numeración. | Todo, incluida la excepción al piso de rentabilidad.           | Emitir, registrar pagos y anular.                 |
| Agrónomo      | Solo lectura del conjunto vigente y de la identidad.                                                       | Crear, editar y emitir dentro de su tope de descuento.         | Solo consulta.                                    |
| Extensionista | Sin acceso.                                                                                                | Consultar las estimaciones de las fincas de su zona.           | Sin acceso.                                       |
| Cliente       | Sin acceso.                                                                                                | Ver y descargar sus cotizaciones emitidas; aceptar o rechazar. | Ver y descargar los suyos; no ve costos internos. |

Los valores de costo interno —mano de obra, factor prestacional, margen— nunca se exponen al rol Cliente, ni en la interfaz ni en la respuesta de la API.

## 13. Gobierno de parámetros

- **Un solo conjunto publicado vigente** por fecha. Publicar uno nuevo cierra la vigencia del anterior sin borrarlo.
- **Doble control.** Editor y aprobador deben ser usuarios distintos; la validación es del servidor, no de la interfaz.
- **Validación previa obligatoria.** No se publica un conjunto con tramos solapados, factores sin opciones, servicios sin componentes o política sin margen.
- **Simulación obligatoria.** Publicar exige haber corrido al menos un caso en el simulador sobre el borrador.
- **Sin efecto retroactivo.** Publicar nunca modifica estimaciones ya emitidas.
- **Trazabilidad.** Cada cambio registra valor anterior, valor nuevo, usuario, fecha y motivo en la bitácora existente.

## 14. Requisitos no funcionales

| ID     | Requisito                       | Meta verificable                                                                                                  |
|--------|---------------------------------|-------------------------------------------------------------------------------------------------------------------|
| RNF-01 | Desempeño del cálculo.          | p95 \< 300 ms para una finca con hasta 10 lotes y 5 servicios.                                                    |
| RNF-02 | Determinismo.                   | Mismo contexto y mismo snapshot → mismo total, en cualquier momento.                                              |
| RNF-03 | Precisión monetaria.            | Decimal de precisión fija; prohibido el uso de punto flotante en la cadena de cálculo.                            |
| RNF-04 | Cobertura de pruebas del motor. | ≥ 90% de líneas en el paquete de cálculo, con los casos de la sección 15 como pruebas de regresión.               |
| RNF-05 | Auditoría.                      | 100% de mutaciones de parámetros y estimaciones registradas y consultables.                                       |
| RNF-06 | Accesibilidad.                  | WCAG 2.1 AA en las nuevas pantallas: foco visible, navegación por teclado, contraste.                             |
| RNF-07 | Responsividad y PWA.            | Operable desde teléfono en campo; consistente con la SPA existente.                                               |
| RNF-08 | Localización.                   | Formato de moneda colombiana y separadores de miles en interfaz y exportaciones.                                  |
| RNF-09 | Compatibilidad.                 | Sin cambios que rompan los endpoints y pantallas actuales; migraciones reversibles.                               |
| RNF-10 | Seguridad.                      | Autorización verificada en el servidor por cada endpoint; sin evaluación de expresiones provistas por el usuario. |
| RNF-11 | Observabilidad.                 | Registro estructurado de cada cálculo con identificador de conjunto y tiempo de respuesta.                        |
| RNF-12 | Documentación.                  | OpenAPI actualizado y manual de administrador en el menú de Ayuda existente.                                      |

## 15. Casos de aceptación del motor

El conjunto semilla se carga con estos valores: tarifa base $100.000; tramos 1–15 a $15.000, 16–30 a $10.000, 31 en adelante a $7.000; factor de dificultad 0% plano, 15% pendiente moderada, 30% acceso difícil; sin margen, sin descuento, sin redondeo. Con esa configuración, el motor **debe** producir exactamente:

| Caso  | Lote                     | Puntos | Dificultad | Total esperado | Costo/punto | Costo/ha  |
|-------|--------------------------|--------|------------|----------------|-------------|-----------|
| CA-01 | 1 ha, plano              | 10     | 0%         | $250.000      | $25.000    | $250.000 |
| CA-02 | 5 ha, pendiente moderada | 8      | 15%        | $253.000      | $31.625    | $50.600  |
| CA-03 | 20 ha, acceso difícil    | 20     | 30%        | $487.500      | $24.375    | $24.375  |
| CA-04 | 50 ha, plano             | 35     | 0%         | $510.000      | $14.571    | $10.200  |

Tolerancia cero en el total. El costo por punto se redondea al peso. Además se validará:

- **CA-05** — Cambiar la tarifa base a $120.000 en un conjunto nuevo y verificar que CA-01 pasa a $270.000 sin desplegar código.
- **CA-06** — Agregar un cuarto tramo (51+ a $5.000) y cotizar 60 puntos correctamente.
- **CA-07** — Recalcular CA-03 con el snapshot después de publicar un conjunto nuevo: el total sigue siendo $487.500.
- **CA-08** — Intentar publicar con tramos 1–15 y 14–30: el sistema lo rechaza indicando el traslape.
- **CA-09** — Emitir con un descuento superior al tope del rol Agrónomo: rechazado con `DESCUENTO_EXCEDE_TOPE`.
- **CA-10** — Cargar un logo nuevo y cambiar el teléfono de contacto; el PDF regenerado muestra ambos cambios sin desplegar código.
- **CA-11** — Agregar un segundo teléfono con etiqueta «WhatsApp» y verificar que aparece en el encabezado del PDF en el orden configurado.
- **CA-12** — Convertir CA-03 en documento de cobro: hereda las líneas y el total de $487.500, recibe consecutivo y queda enlazado a la estimación.
- **CA-13** — Registrar un abono parcial: el saldo se recalcula y el estado pasa a «pagado parcialmente»; al completar el saldo pasa a «pagado».
- **CA-14** — Anular un documento emitido: no desaparece, queda con motivo y usuario, y la estimación admite un documento nuevo.
- **CA-15** — Intentar emitir con la numeración agotada: rechazado con `NUMERACION_AGOTADA` y aviso al administrador.

## 16. Integraciones con lo ya construido

| Módulo existente    | Relación                                                                                                        |
|---------------------|-----------------------------------------------------------------------------------------------------------------|
| Comisiones          | Destino natural de la estimación aceptada: precarga equipo, fechas y valor, y conserva la referencia de origen. |
| Lista de trabajos   | Nueva etapa previa «estimación» antes de «comisión» en el semáforo de la orden de trabajo.                      |
| Equipo de trabajo   | Fuente de las tarifas por rol y día para el cálculo del costo interno; no se duplica el catálogo.               |
| Administrar insumos | Fuente de precios de consumibles cuando el componente los referencia.                                           |
| Fincas y lotes      | Fuente de área, coordenadas, pedregosidad, profundidad efectiva y tipo de riego para precargar las condiciones. |
| Auditoría           | Recibe los eventos de parámetros y estimaciones con las mismas entidades filtrables.                            |
| Reportes            | Reutiliza el mecanismo de exportación por audiencia para la cotización del cliente.                             |
| Recomendaciones     | Sin acoplamiento: la regla actual de «finca con comisión» permanece intacta.                                    |

## 17. Cotización en PDF y documento de cobro

### Composición del PDF

Un solo motor de composición para los dos documentos, cambiando la plantilla y el bloque de totales. Todo el contenido variable proviene de parámetros o del snapshot; la plantilla no contiene ningún dato de la empresa escrito directamente.

    ┌──────────────────────────────────────────────────────────────┐
    │  [logo AgroIA]        Nombre comercial · NIT                  │
    │                       sitio web · teléfonos · correo · ciudad │  ← P-14
    ├──────────────────────────────────────────────────────────────┤
    │  COTIZACIÓN COT-2026-00184        Emitida: 18/09/2026         │
    │  Válida hasta: 18/10/2026         Asesor: …                   │
    ├──────────────────────────────────────────────────────────────┤
    │  Cliente: …            Finca: …        Municipio: …           │
    │  Lotes y área: …                                              │
    ├──────────────────────────────────────────────────────────────┤
    │  Servicio        Cant.  Unidad   Vr. unitario      Valor      │
    │  … desglose línea por línea, agrupado por lote …              │
    ├──────────────────────────────────────────────────────────────┤
    │  Subtotal · Recargos · Descuento · Impuestos · TOTAL          │
    ├──────────────────────────────────────────────────────────────┤
    │  Condiciones comerciales · forma y plazo de pago              │
    │  Términos y condiciones · pie legal                           │  ← P-14 / P-15
    └──────────────────────────────────────────────────────────────┘

Requisitos de la plantilla: tamaño carta, márgenes aptos para impresión, numeración «página X de Y», logo en vectorial cuando el archivo cargado sea SVG, y degradación correcta si el logo no está configurado —se imprime el nombre comercial, no un marco vacío ni un error—.

### De la cotización al cobro

El documento de cobro no es una edición de la cotización: es un documento nuevo que hereda sus líneas y queda enlazado a ella. La cotización sigue siendo evidencia de lo ofertado; el cobro es evidencia de lo exigido.

    estimación aceptada ──► documento de cobro ──► pagos ──► saldo cero
            │                      │                            │
            │                      ├── anulación con motivo      │
            └── comisión ──────────┴── nunca se borra ───────────┘

- Solo una estimación en estado **aceptada** y no vencida puede convertirse en documento de cobro.
- Una estimación genera **un único** documento vigente; si se anula, se puede emitir uno nuevo con referencia al anulado.
- El consecutivo se asigna en el servidor con bloqueo, al emitir, no al crear el borrador.
- Emitido el documento, sus valores quedan inmutables; toda corrección es anulación más documento nuevo.
- El sistema bloquea la emisión si la numeración se agotó o la resolución venció, y avisa con anticipación configurable.

> **Decisión pendiente que el proveedor debe plantear en su propuesta.** En Colombia, una *factura de venta* exige validación previa ante la DIAN —XML UBL 2.1, CUFE, proveedor tecnológico autorizado— mientras que una *cuenta de cobro* no. Esta contratación cubre la generación del documento, la numeración controlada y el seguimiento de pago; la habilitación DIAN se aborda después. Por eso el modelo de datos ya reserva `cufe` y `xml_url`: el día que se integre el proveedor tecnológico no debe haber migración destructiva. La propuesta debe indicar qué tipo de documento habilitaría primero y cómo dejaría preparado el otro.

## 18. Fases de entrega

| Fase | Contenido                                                                                        | Cierra con                                                        |
|------|--------------------------------------------------------------------------------------------------|-------------------------------------------------------------------|
| F1   | Modelo de datos, motor de cálculo, conjunto semilla y API de simulación.                         | CA-01 a CA-04 en verde, ejecutables en integración continua.      |
| F2   | Pantalla de parámetros con versionado, validación, doble control y simulador.                    | CA-05, CA-06 y CA-08 en verde; manual de administrador publicado. |
| F3   | Cotizador, ciclo de vida de la estimación, snapshot, márgenes y descuentos.                      | CA-07 y CA-09 en verde; exportación HTML funcionando.             |
| F4   | Identidad administrable y generación del PDF de la cotización.                                   | CA-10 y CA-11 en verde; PDF impreso y revisado en papel.          |
| F5   | Documento de cobro, numeración consecutiva, pagos y anulación.                                   | CA-12 y CA-13 en verde; flujo cotización → cobro → pago cerrado.  |
| F6   | Conversión a comisión, integración con lista de trabajos y auditoría.                            | Flujo completo finca → estimación → comisión → orden de trabajo.  |
| F7   | Opcionales: cálculo offline, importación/exportación de parámetros, envío por WhatsApp, tablero. | Según priorización conjunta al cierre de F6.                      |

Se espera entrega incremental con ambiente de pruebas disponible al final de cada fase y demostración funcional en vivo, no presentación de diapositivas.

## 19. Entregables esperados

- Código fuente en el repositorio del proyecto, con la convención de ramas vigente.
- Migraciones de base de datos reversibles y script del conjunto de parámetros semilla.
- Suite de pruebas automatizadas del motor, incluidos los casos CA-01 a CA-09.
- OpenAPI actualizado y colección de peticiones de ejemplo.
- Manual de administrador para la pantalla de parámetros, integrado al menú de Ayuda.
- Documento de decisiones de arquitectura con las desviaciones respecto de esta propuesta y su justificación.
- Sesión de transferencia de conocimiento grabada, de una hora como mínimo.

## 20. Supuestos, riesgos y dependencias

| Asunto                                                                            | Tratamiento esperado                                                                                                                         |
|-----------------------------------------------------------------------------------|----------------------------------------------------------------------------------------------------------------------------------------------|
| Las tarifas del estudio son ilustrativas, no validadas por el mercado colombiano. | Cargarlas como conjunto semilla claramente marcado como provisional, sustituible el primer día de operación.                                 |
| Un parámetro mal configurado puede producir cotizaciones ruinosas o inviables.    | Validación previa, simulación obligatoria, doble control y piso de rentabilidad.                                                             |
| Tentación de resolver casos particulares con condicionales en el código.          | Toda excepción de negocio debe expresarse como componente condicional parametrizado; el código no conoce cultivos ni municipios específicos. |
| Deriva de precios por inflación.                                                  | Reajuste masivo con vista previa y aviso de vencimiento del conjunto.                                                                        |
| Distancia por carretera vs. distancia en línea recta.                             | Primera versión con distancia geodésica y km editables; ruteo real queda como opcional.                                                      |
| Volumen de datos histórico.                                                       | Las estimaciones no se depuran: el snapshot es evidencia contractual.                                                                        |

## 21. Formato de la propuesta

La propuesta debe ser breve y verificable. Se solicita:

1.  Entendimiento del problema en máximo dos páginas, señalando lo que haría distinto de esta especificación y por qué.
2.  Enfoque técnico: modelo de datos propuesto, diseño del motor y estrategia de pruebas.
3.  Plan de trabajo por fases con fechas, hitos y criterios de cierre.
4.  Equipo asignado con perfiles, dedicación y experiencia verificable en motores de tarifas o reglas parametrizables.
5.  Propuesta económica desglosada por fase, con tarifas y supuestos de esfuerzo.
6.  Riesgos identificados por el proveedor y su plan de mitigación.
7.  Dos referencias de trabajos comparables, con contacto verificable.
8.  Modelo de soporte y garantía posterior a la entrega.

## 22. Criterios de evaluación

| Criterio                                             | Peso | Qué se valora                                                                   |
|------------------------------------------------------|------|---------------------------------------------------------------------------------|
| Solidez técnica del motor y del modelo de parámetros | 30%  | Determinismo, extensibilidad sin despliegue, ausencia de valores en código.     |
| Comprensión del dominio agronómico y comercial       | 20%  | Manejo de densidad de muestreo, dilución del costo fijo y piso de rentabilidad. |
| Calidad de la experiencia de administración          | 15%  | Que un administrador no técnico opere el simulador y publique sin ayuda.        |
| Plan, equipo y capacidad de entrega                  | 15%  | Realismo del cronograma y dedicación efectiva del equipo.                       |
| Propuesta económica                                  | 15%  | Relación valor-alcance, no precio más bajo.                                     |
| Soporte, garantía y transferencia                    | 5%   | Continuidad después del cierre del contrato.                                    |

Descalifica automáticamente cualquier propuesta cuyo diseño requiera modificar código para cambiar una tarifa, un tramo, un recargo o una regla de densidad.

RFP AGC-COST · AgroIA · AGROINTELIGENTE COLOMBIA · versión 1.0 · 18 de septiembre de 2026. Las cifras de referencia provienen del estudio interno de tarifas de muestreo en grilla y son ilustrativas; no constituyen tarifa de mercado confirmada.
