# AgroIA — Catálogo funcional detallado

> **Propósito:** describir las capacidades visibles y de negocio de AgroIA a partir de la
> aplicación web y los módulos registrados en el backend del repositorio.
> **Alcance revisado:** SPA `apps/frontend-web/` y routers de
> `apps/backend/agroia_backend/api/`. Las rutas se muestran como referencias de integración,
> no como contrato exhaustivo. Para los modelos de datos y comportamiento interno, consulta
> [el documento funcional-técnico](../architecture/Documento_Funcional_Tecnico_AgroIA.md).
> El menú puede variar según el rol y la configuración del despliegue.

## 1. Resumen del producto

AgroIA es una plataforma de apoyo a la gestión agrícola que reúne información de fincas,
mediciones de suelo, clima y operación de campo para ayudar a agricultores, agrónomos,
extensionistas y administradores. Sus capacidades funcionales incluyen:

- Gestión de usuarios, perfiles y acceso a fincas.
- Registro geográfico de fincas, lotes y ciclos productivos.
- Recepción de mediciones desde dispositivos, cargas de archivos y sincronización diferida.
- Diagnóstico de suelo y recomendaciones de aptitud, cultivo y manejo.
- Catálogo agrícola, fichas técnicas, variedades y curvas de extracción.
- Paneles, alertas, reportes descargables y asesoría conversacional.
- Gestión de agua y riego, monitoreo de plagas, análisis de laboratorio y BPA.
- Operación administrativa y comercial: equipos, comisiones, órdenes de trabajo, costeo,
  estimaciones, cotizaciones y documentos de cobro.

La aplicación web de referencia está implementada como SPA en `apps/frontend-web/` y el
backend principal expone servicios HTTP bajo `/api/v1`. El repositorio también contiene un
frontend Angular y servicios/componentes adicionales; no se debe asumir que cada uno se
despliega o está habilitado en todos los ambientes.

## 2. Perfiles y alcance de acceso

El menú de la SPA configura cuatro perfiles de uso:

| Perfil | Capacidades principales |
|---|---|
| **Administrador** | Acceso operativo y administrativo: fincas, usuarios, catálogo, insumos, precios, BPA, equipos, comisiones, trabajos, costeo y mantenimiento de modelos. |
| **Agrónomo** | Análisis y asesoría técnica: sensores, carga de mediciones, recomendaciones, historial, reportes, catálogo, visión de plagas y estimaciones de costos. |
| **Cliente / agricultor** | Consulta de sus fincas y alertas, reportes, asesoría y funcionalidades comerciales disponibles para su cuenta, como cotizaciones. Las escrituras agronómicas y administrativas están restringidas. |
| **Extensionista** | Consulta de fincas de su zona, alertas, sensores, historial, reportes, catálogo y diagnóstico visual. El ámbito territorial depende de la asignación del perfil. |

Las autorizaciones efectivas se validan en el backend y pueden ser más restrictivas que la
visibilidad de un control. Las pantallas no sustituyen la autorización del servidor. La
documentación existente menciona otros perfiles auxiliares, pero el menú principal y sus
permisos deben comprobarse para cada despliegue.

## 3. Funcionalidades para el trabajo agrícola

### 3.1 Inicio y panel de finca

Presenta una vista resumida de la finca seleccionada y permite orientar el trabajo diario.
Según la información disponible, puede reunir:

- Clasificación agronómica y semáforo de aptitud/confianza de la última recomendación.
- Indicadores de suelo como pH, nitrógeno, fósforo, potasio y conductividad eléctrica cuando
  existen lecturas.
- Alertas asociadas a la finca, últimas lecturas de sensores y tareas pendientes.
- Estado del ciclo productivo activo y acceso a su registro de cosecha.
- Información de necesidad de riego/pronóstico cuando existen los datos y servicios requeridos.
- Exportación de datos del panel para análisis externo.

**Referencia de API:** `GET /api/v1/dashboard/{finca_id}`; exportación en
`/api/v1/dashboard/{finca_id}/export`.

### 3.2 Fincas, ubicación y lotes

La gestión de fincas estructura los datos productivos por predio y lote.

- Registrar una finca con información básica, propietario/contacto, departamento y municipio.
- Obtener o actualizar la localización, incluida georreferenciación y consulta de coordenadas.
- Incorporar área, linderos, datos físicos del predio y propiedades agronómicas disponibles.
- Consultar, editar y, con permiso, eliminar fincas.
- Crear y mantener lotes vinculados a una finca, con sus datos de suelo y dimensiones.
- Consultar el enriquecimiento geográfico/SIG cuando hay fuentes de referencia configuradas.
- Resolver enlaces de mapas, consultar geocodificación y elevación mediante los servicios
  disponibles.

**Referencia de API:** `/api/v1/fincas`, `/api/v1/fincas/{finca_id}/lotes`,
`/api/v1/location/*` y `/api/v1/fincas/{finca_id}/enriquecimiento-sig`.

### 3.3 Dispositivos, sensores e ingreso de mediciones

AgroIA permite incorporar observaciones de campo de varias maneras:

- Recibir tramas enviadas por sensores IoT y asociarlas al dispositivo/finca correspondiente.
- Registrar y consultar dispositivos vinculados a las fincas.
- Revisar lecturas históricas y estado reciente de transmisión del sensor.
- Probar el formato de una trama desde el simulador de la interfaz cuando está disponible.
- Cargar archivos CSV, TXT o JSON para incorporar mediciones capturadas fuera de línea.
- Normalizar unidades/formato antes de guardar mediciones y usarlas en el análisis.
- Consultar datos de fuentes externas para complementar la información, sujeto a disponibilidad
  de las integraciones configuradas.
- Sincronizar lecturas pendientes cuando el cliente recupera conectividad.

**Referencia de API:** `POST /api/sensor`, `/api/v1/iot/ingest`,
`/api/v1/iot/carga`, `/api/v1/iot/dispositivos`, `/api/v1/iot/lecturas/{finca_id}` y
`/api/v1/iot/sensores/{finca_id}/status`.

### 3.4 Diagnóstico y recomendaciones agronómicas

Es el flujo central de análisis. El usuario con permisos selecciona una finca y puede indicar
un cultivo específico. El análisis puede operar en dos contextos:

1. **Aptitud/selección de cultivo:** comparar opciones y priorizar cultivos según la información
   agronómica disponible.
2. **Diagnóstico de un cultivo:** evaluar el cultivo seleccionado y presentar acciones
   relacionadas con las variables del suelo.

La respuesta puede incluir:

- Clasificación de aptitud y nivel de confianza/validación.
- Variables disponibles, faltantes, fuera de rango o sujetas a confirmación.
- Comparación con rangos objetivo, acciones recomendadas, prioridad y contexto agronómico.
- Revisión de interacciones o antagonismos entre nutrientes y advertencias que condicionan la
  recomendación a confirmar un dato con análisis de laboratorio.
- Ranking de cultivos sugeridos y reglas aplicadas cuando el caso corresponde a selección.
- Información fenológica y de desarrollo cuando el cultivo tiene esos datos.
- Plan económico de fertilización, si se proporcionan presupuesto y precios configurados.
- Advertencias de calidad, incertidumbre o necesidad de revisión profesional.
- Registro de la aceptación humana de una recomendación por perfiles técnicos autorizados.

El documento técnico del repositorio describe un motor híbrido: las reglas agronómicas
fundamentan la recomendación publicada y los modelos de Machine Learning se ejecutan en modo
de contraste/sombra para evaluar concordancia mientras esa configuración se mantenga.

El resultado es una ayuda a la decisión: una clasificación automática o un diagnóstico visual
no debe interpretarse como certificación, prescripción infalible ni reemplazo de la evaluación
de un profesional. La salida depende de la calidad, actualidad y cobertura de los datos.

**Referencia de API:** `POST /api/v1/recomendaciones/analyze`,
`POST /api/v1/recomendaciones/aceptar` y
`GET /api/v1/recomendaciones/historial/{finca_id}`.

### 3.5 Historial y ciclos productivos

Permite conservar el contexto temporal de los lotes y cultivos:

- Consultar recomendaciones anteriores por finca y, cuando se indica, por cultivo.
- Registrar el inicio de ciclos y asociarlos a finca/lote/cultivo.
- Consultar el ciclo activo y el historial de ciclos del lote.
- Actualizar datos de un ciclo y registrar su cosecha/cierre.
- Importar historiales de ciclo desde un archivo CSV cuando la interfaz y permisos lo permiten.
- Vincular rendimiento, fechas y otros datos de producción disponibles a la trazabilidad.

**Referencia de API:** `/api/v1/fincas/{finca_id}/lotes/{lote_id}/ciclos`,
`/api/v1/fincas/{finca_id}/ciclo/activo`, `/api/v1/fincas/{finca_id}/ciclo/cosechar`
y `/api/v1/fincas/{finca_id}/ciclos/carga-csv`.

### 3.6 Catálogo, fichas, variedades y extracción de nutrientes

El catálogo centraliza información agrícola de consulta y mantenimiento:

- Buscar y consultar cultivos y sus datos agronómicos disponibles.
- Administrar fichas técnicas, con un proceso de envío a revisión y aprobación/rechazo.
- Consultar variedades asociadas a un cultivo.
- Consultar o mantener curvas de extracción cuando están definidas.
- Utilizar información de cultivo para fundamentar recomendaciones, análisis económicos y
  seguimiento fenológico.

El número de cultivos, fichas y variedades visibles depende del contenido vigente de la base de
datos y de los permisos.

**Referencia de API:** `/api/v1/catalogo/cultivos`, `/api/v1/catalogo/fichas`,
`/api/v1/cultivos/{cultivo_id}/variedades` y
`/api/v1/cultivos/{cultivo_id}/curva-extraccion`.

### 3.7 Reportes, exportación y simulación

Los reportes compilan información de finca, análisis agronómico y otros componentes habilitados.
Entre las opciones documentadas se encuentran:

- Generar reportes orientados a siembra, cultivo o una vista completa.
- Previsualizar el resultado en la aplicación y abrir/descargar el HTML.
- Imprimir el reporte para guardarlo como PDF.
- Seleccionar una presentación para agricultor o agrónomo cuando la opción está disponible.
- Incluir datos de suelo, diagnóstico, recomendaciones, ranking, elementos económicos y datos
  operativos disponibles para esa finca.
- Presentar visualizaciones como mapa de calor o plano del lote, y secciones de clima, riego,
  rotación, BPA y labores cuando el reporte correspondiente cuenta con esos datos.
- Simular escenarios o cambios de parámetros para comparar resultados sin convertirlos en
  mediciones observadas.
- Exportar información del panel en formatos admitidos por la funcionalidad.

El contenido de un reporte puede variar con el tipo seleccionado, el rol, la existencia de
recomendaciones, la configuración regional y la disponibilidad de datos.

**Referencia de API:** `POST /api/v1/reportes/generar`,
`POST /api/v1/reportes/simular` y las rutas de reporte/exportación del dashboard.

### 3.8 Asesoría conversacional (chat)

El chat permite formular preguntas relacionadas con el contexto agrícola disponible para una
finca y continuar conversaciones asociadas a ella. La implementación contempla una base de
conocimiento/recuperación de contexto y memoria de conversación por finca; los resultados
dependen de la configuración de los proveedores y documentos disponibles. En algunas pantallas
se contempla adjuntar una imagen.

El chat responde en dos modos según la configuración del entorno:

- **LLM (OpenAI):** si `OPENAI_API_KEY` está configurada con una clave válida, la respuesta la
  genera el modelo con un *system prompt* de experto agrónomo y el contexto real de la finca
  (lectura de suelo, reglas, ficha técnica, análisis y clima). No se trata de un modelo
  entrenado: es *prompt engineering* sobre el contexto.
- **Experto local:** sin clave, un motor determinista responde con reglas agronómicas y la
  lectura de suelo. Cubre intenciones de fecha, concepto/significado de variables (pH,
  nutrientes, materia orgánica, etc.), ubicación de la finca, clima/época, siembra, abono,
  riego, encalado, diagnóstico de problemas y explicación de reportes. Solo usa datos del
  contexto y declara explícitamente cuando no tiene un dato o una fuente externa (p. ej.
  pronóstico IDEAM). No requiere reentrenamiento: se amplía agregando intenciones/reglas.

El chat solo está disponible cuando el usuario selecciona una finca en el reporte; sin finca
seleccionada se le solicita elegir una antes de consultar.

### 3.8.1 Interacción por voz (RFP-AGROIA-001)

La captura de voz permite dictar la consulta al Asesor agronómico además de escribirla:

- Botón de micrófono junto al campo de texto, con estados **inactivo · grabando · procesando ·
  error** e indicador de nivel de audio.
- Permiso de micrófono solicitado solo al activar la función, con orientación si se deniega.
- Detención manual o por silencio (2 s) y duración máxima configurable (60 s por defecto).
- Transcripción **híbrida**: Web Speech API del navegador por defecto y transcripción en
  servidor como respaldo cuando el navegador no la soporta o falla.
- La transcripción se inserta en el campo de texto para revisión y edición; **no se envía
  automáticamente**.
- Comandos de control por voz: **“enviar”**, **“borrar”**, **“cancelar”** y **“repetir”**
  (reconocidos solo cuando se pronuncian solos).
- Degradación elegante: ante falta de soporte, permisos denegados, sin conexión o error de
  transcripción se informa y el flujo de escritura sigue disponible.
- El audio no se almacena; se transmite cifrado (HTTPS) y se descarta al terminar la
  transcripción.

**Administración de la función (rol administrador):**

- Activar/desactivar la voz, configurar duración máxima e idioma desde
  **Administración → Parámetros de voz**.
- Consultar métricas agregadas mensuales de uso (consultas por voz, errores y duración media)
  desde **Administración → Métricas de voz**, sin audio ni contenido de consultas.

**Referencia de API:** `POST /api/v1/chat/consultar`,
`GET /api/v1/chat/memoria/{finca_id}`, `POST /api/v1/voz/transcripcion`,
`GET|PUT /api/v1/voz/parametros` y `GET|POST /api/v1/voz/metricas`.

### 3.9 Clima, alertas y calendario lunar

- Consultar alertas activas para las fincas permitidas al perfil.
- Consultar clima actual y pronóstico si las fuentes externas están configuradas y responden.
- Evaluar alertas climáticas automáticamente o mediante una acción administrativa disponible.
- Consultar calendario lunar (Almanaque Bristol), fase actual, pronóstico y calendario mensual.
- Mantener preferencias de usuario relacionadas con alertas de calendario lunar.
- Consultar alertas de lluvia u otras condiciones de riesgo agrícola cuando se cumplen las reglas
  y existe información suficiente.

**Referencia de API:** `/api/v1/alertas-climaticas`,
`/api/v1/fincas/{finca_id}/clima`, `/api/v1/calendario-lunar/*` y
`/api/v1/usuarios/preferencias-bristol`.

### 3.10 Agua, balance hídrico y riego

La aplicación dispone de servicios para registrar/consultar análisis o parámetros relacionados
con agua y riego, además de consultar el balance hídrico de una finca. Estos datos pueden
complementar el análisis de necesidades de riego y las vistas operativas. Los cálculos y
resultados dependen de las entradas, los modelos meteorológicos disponibles y la configuración
del despliegue.

**Referencia de API:** `/api/v1/fincas/{finca_id}/agua-riego` y
`/api/v1/fincas/{finca_id}/balance-hidrico`.

### 3.11 Análisis de laboratorio y calidad de suelo

Permite ingresar los resultados de análisis de laboratorio asociados a una finca, consultarlos
y eliminar registros según los permisos. Los resultados sirven como referencia adicional para
interpretar mediciones y mejorar la calidad del diagnóstico.

**Referencia de API:** `/api/v1/fincas/{finca_id}/lab/ingestar` y
`/api/v1/fincas/{finca_id}/lab/analisis`.

### 3.12 Monitoreo y diagnóstico visual de plagas

El dominio contempla dos funciones complementarias:

- **Monitoreo de plagas por lote:** registrar y consultar observaciones de campo.
- **Diagnóstico por imagen:** enviar una fotografía para obtener una evaluación visual
  preliminar, consultar diagnósticos asociados a la finca y confirmar una etiqueta con el rol
  técnico autorizado.

La clasificación visual es orientativa y puede abstenerse o requerir validación humana. La
calidad de la imagen, las clases disponibles y los modelos instalados limitan el resultado.

**Referencia de API:** `/api/v1/fincas/{finca_id}/lotes/{lote_id}/monitoreo-plagas`,
`/api/v1/vision/diagnose`, `/api/v1/vision/diagnosticos/{finca_id}` y la operación de
confirmación de diagnóstico.

### 3.13 Rotación de cultivos

El backend ofrece una recomendación de rotación por finca. Esta capacidad utiliza la información
de cultivos/ciclos que se encuentre registrada para sugerir una secuencia o alternativa; debe
interpretarse según la cobertura histórica de los datos.

**Referencia de API:** `/api/v1/fincas/{finca_id}/recomendacion-rotacion`.

### 3.14 Buenas Prácticas Agrícolas (BPA) y trazabilidad

Para perfiles autorizados, las funciones BPA permiten:

- Consultar y actualizar el checklist de la finca.
- Registrar y consultar visitas de verificación.
- Consultar un reporte de trazabilidad relacionado con la finca.

El checklist es una herramienta de seguimiento y no acredita por sí mismo una certificación
oficial.

**Referencia de API:** `/api/v1/fincas/{finca_id}/bpa/checklist`,
`/api/v1/fincas/{finca_id}/bpa/visitas` y
`/api/v1/fincas/{finca_id}/bpa/reporte-trazabilidad`.

### 3.15 Labores y órdenes de trabajo

Las labores representan acciones operativas asociadas a las fincas:

- Generar labores/órdenes a partir del contexto de la finca.
- Consultar las labores y las tareas pendientes para el día.
- Actualizar su estado o información.
- Asociar evidencia fotográfica cuando la operación está habilitada.
- Sincronizar registros capturados mientras el dispositivo estaba desconectado.

**Referencia de API:** `/api/v1/fincas/{finca_id}/labores`,
`/api/v1/fincas/{finca_id}/labores/pendientes-hoy` y las operaciones de generación y edición
de labores.

## 4. Funciones administrativas, comerciales y de operación

### 4.1 Usuarios, perfiles y membresías

- Registrar una cuenta y consultar/actualizar los datos propios habilitados.
- Consultar información de membresía asociada a una cuenta.
- Para administración autorizada: listar, crear, editar, cambiar rol y desactivar/eliminar
  usuarios según las reglas vigentes.
- Asociar el alcance de fincas visible para los usuarios cuando corresponde.

**Referencia de API:** `/api/v1/usuarios/*`, `/api/v1/admin/usuarios*` y
`/api/v1/auth/*`.

### 4.2 Equipo de trabajo

Administra la estructura de personal de campo:

- Crear, editar, consultar y retirar empleados del equipo.
- Consultar y actualizar tarifas por rol.
- Registrar novedades de empleados y cerrar novedades abiertas.
- Incorporar reemplazos cuando el flujo administrativo lo permite.

**Referencia de API:** `/api/v1/admin/equipo-trabajo*`.

### 4.3 Comisiones y lista de trabajos

- Crear y administrar comisiones asociadas a fincas, etapas, equipo, fechas y valores.
- Finalizar o retirar comisiones según los permisos disponibles.
- Consultar la lista de trabajos y la etapa de avance de las fincas en el flujo operativo.
- Usar el estado del flujo para coordinar tareas, toma de muestras, recomendaciones y entrega
  de reportes cuando esa configuración esté habilitada.

**Referencia de API:** `/api/v1/admin/comisiones*` y
`GET /api/v1/admin/lista-trabajos`.

### 4.4 Costeo parametrizado (AGC-COST)

El módulo de costeo permite separar los parámetros comerciales de los cálculos:

- Consultar los parámetros vigentes y simular el costo de un servicio/escenario.
- Administrar conjuntos de parámetros: crear, modificar, validar, publicar, archivar o clonar.
- Configurar servicios, componentes, tramos, factores y opciones.
- Administrar elementos asociados como densidad, zonas, impuestos, descuentos y políticas.
- Importar o exportar conjuntos para respaldar o trasladar la configuración.
- Controlar la publicación del conjunto para distinguir borradores de parámetros vigentes.

**Referencia de API:** `/api/v1/costeo/parametros/vigentes`,
`POST /api/v1/costeo/simular` y operaciones de administración bajo `/api/v1/costeo/*`.

### 4.5 Estimaciones, cotizaciones y documentos de cobro

Las herramientas comerciales incluyen:

- Crear, consultar, modificar y recalcular estimaciones de costos.
- Consultar tablero de estimaciones y sugerencias auxiliares de puntos/distancias cuando
  corresponda.
- Emitir una estimación, registrar su aceptación o rechazo y convertirla en comisión cuando el
  flujo lo permite.
- Exportar una estimación.
- Crear y consultar documentos de cobro; emitirlos, registrar pagos, anularlos o enviarlos.
- Obtener representación PDF/exportable de documentos de cobro.
- Consultar cotizaciones propias en la vista de cliente cuando esté habilitada.
- Configurar identidad comercial, logotipo y datos de cobro desde la funcionalidad
  administrativa asociada.

**Referencia de API:** `/api/v1/estimaciones*`, `/api/v1/cobros*`,
`/api/v1/costeo/identidad*` y `/api/v1/costeo/cobro-config`.

### 4.6 Precios de insumos y cosecha

- Administrar precios de insumos usados por las estimaciones económicas de manejo.
- Consultar precios de cosecha por cultivo y ubicación, y mantener esos valores desde el perfil
  administrativo.
- Utilizar los datos disponibles para contextualizar costo, retorno o rentabilidad estimada.

Los valores de referencia pueden estar incompletos o desactualizados; una estimación no equivale
a una oferta comercial ni garantiza un precio de mercado.

**Referencia de API:** `/api/v1/admin/precios-insumos`,
`GET /api/v1/cultivos/precios` y `PUT /api/v1/admin/precios-cosecha`.

### 4.7 Administración de modelos y datos de validación

- Consultar el estado del componente de Machine Learning y etiquetas/ejemplos de validación
  disponibles.
- Encolar procesos de reentrenamiento cuando se cuenta con permisos y el proceso está
  configurado.
- Consultar el estado del conjunto de datos utilizado por la función de visión y solicitar
  reentrenamiento desde operaciones administrativas disponibles.
- Incorporar confirmaciones humanas al flujo de evaluación cuando esté implementado.

La existencia de una ruta de administración no implica que haya un modelo entrenado, una tarea
en ejecución o capacidad de cómputo disponible en el ambiente.

**Referencia de API:** rutas `/api/v1/ml/*`, estado de ML y etiquetas doradas; operaciones
administrativas del módulo de visión.

### 4.8 Auditoría y mantenimiento

- Consultar una bitácora de acciones administrativas y operativas, con filtros compatibles con
  la pantalla.
- Ejecutar operaciones de mantenimiento o reinicio del conjunto de demostración solo desde
  rutas administrativas habilitadas.
- Consultar salud de servicios y sincronización.

Las acciones que modifican información deben estar sujetas a autorización y quedar registradas
cuando la auditoría esté configurada.

**Referencia de API:** `GET /api/v1/auditoria`, `/api/v1/admin/*`,
`/api/v1/demo/*` y `/api/v1/health`.

## 5. Funciones transversales de la aplicación

### 5.1 Inicio de sesión y continuidad de sesión

- Inicio de sesión con credenciales.
- Renovación de sesión mediante refresh token desde la SPA cuando recibe una respuesta de
  autorización vencida.
- Consulta de identidad y rol actual.
- Cierre de sesión y limpieza de la sesión local.

Las credenciales de demostración no forman parte de este catálogo y no deben publicarse en
documentación versionada. Su provisión pertenece a la configuración segura de cada entorno.

**Referencia de API:** `/api/v1/auth/login`, `/api/v1/auth/refresh`,
`/api/v1/auth/logout` y `/api/v1/auth/me`.

### 5.2 Modo PWA y trabajo sin conexión

La SPA incluye un service worker y funciones de operación offline. Cuando están disponibles,
permiten conservar registros pendientes localmente y sincronizarlos al recuperar conectividad.
El backend dispone de operaciones de sincronización para lecturas de sensores y labores, además
de consulta de estado.

El modo offline no garantiza que todas las pantallas, reportes o análisis estén disponibles sin
red; la sincronización depende de autenticación, conectividad y aceptación del servidor.

**Referencia de API:** `/api/v1/sync/estado`, `/api/v1/sync/sensor-readings` y
`/api/v1/sync/labores`.

### 5.3 Preferencias y notificaciones

Se pueden consultar/actualizar preferencias de notificación por finca y preferencias personales
del calendario lunar. La entrega de notificaciones depende de los canales y servicios que estén
configurados en el despliegue; no se presupone un canal externo concreto.

**Referencia de API:** `/api/v1/fincas/{finca_id}/notificaciones/preferencias` y
`/api/v1/usuarios/preferencias-bristol`.

### 5.4 Integración geográfica y fuentes externas

La plataforma expone utilidades para resolver enlaces de ubicación, geocodificar, consultar
elevación y enriquecer datos geográficos. También contiene servicios para obtener datos
climáticos y fuentes externas. Estas capacidades requieren conectividad, credenciales o
servicios externos según el ambiente.

### 5.5 Resiliencia y observabilidad

El backend incorpora rutas de salud, estado de módulos, validación de entrada y manejo de
errores HTTP. En el cliente, los errores de API se muestran como mensajes de interfaz y, ante
ciertos errores de sesión, se intenta una renovación antes de pedir un nuevo inicio de sesión.
La disponibilidad de métricas, trazas y registros operativos depende de la configuración del
despliegue.

## 6. Recorrido de usuario de extremo a extremo

Un flujo agrícola representativo es:

1. El administrador o usuario autorizado registra una finca y sus lotes.
2. Se asocian dispositivos o se ingresan lecturas desde una carga de archivo o captura offline.
3. El agrónomo revisa los datos y ejecuta un análisis para aptitud o para el cultivo actual.
4. El sistema presenta el diagnóstico, incertidumbres, acciones posibles y contexto económico.
5. El profesional revisa/acepta la recomendación y registra el ciclo o las labores pertinentes.
6. El productor y los perfiles autorizados consultan el panel, las alertas y el reporte.
7. El equipo registra avances, visitas BPA, cosecha y rendimiento para conservar trazabilidad.
8. Las funciones comerciales pueden convertir el trabajo en una estimación, cotización,
   comisión y documento de cobro, según los permisos y configuración.

## 7. Matriz resumida de acceso

| Área | Cliente | Agrónomo | Extensionista | Administrador |
|---|---:|---:|---:|---:|
| Panel, alertas y reportes de fincas permitidas | Consulta | Sí | Sí, por zona | Sí |
| Análisis y aceptación técnica | No como operación técnica | Sí | Según permisos de API | Sí |
| Dispositivos y carga de lecturas | Consulta según acceso | Sí | Consulta/operación permitida | Sí |
| Fincas, lotes y ciclos | Consulta limitada | Consulta | Consulta territorial | Administración |
| Catálogo agrícola | Consulta | Consulta/gestión habilitada | Consulta | Consulta/gestión habilitada |
| Visión y monitoreo de plagas | Consulta disponible según endpoint | Sí | Sí | Sí |
| BPA, personal, comisiones y trabajos | No | No administrativo | Consulta territorial | Administración |
| Costeo, estimaciones y cobros | Funciones propias disponibles | Estimaciones | No según menú | Administración |
| Usuarios, auditoría y configuración | No | No | No | Administración |

Esta tabla es orientativa: las políticas reales pueden restringir una operación o habilitarla
por configuración. La autorización del backend es la fuente efectiva.

## 8. Entidades funcionales principales

- **Usuario y membresía:** identidad, perfil, estado, alcance y permisos.
- **Finca:** unidad productiva, propietario, ubicación y características generales.
- **Lote:** subdivisión productiva de una finca, con características propias.
- **Dispositivo y lectura:** fuente de captura y observación de variables agronómicas/ambientales.
- **Cultivo, ficha y variedad:** catálogo de referencia para análisis y operación agrícola.
- **Recomendación:** resultado de un análisis, con clasificación, variables, acciones y estado de
  validación/aceptación.
- **Ciclo productivo:** período de cultivo en un lote con fechas, rendimiento y cierre.
- **Alerta y preferencia:** evento de riesgo/aviso y reglas de notificación asociadas.
- **Labor y equipo:** acción operativa, empleado, tarifa, novedad y evidencia.
- **Comisión y estimación:** trabajo contratado/propuesto y cálculo de costo relacionado.
- **Documento de cobro y pago:** obligación comercial, emisión y movimientos registrados.
- **Análisis de laboratorio, visita BPA y diagnóstico visual:** evidencia complementaria de
  condición, seguimiento o validación.

## 9. Alcances y consideraciones

- Las funciones que requieren sensores, datos meteorológicos, mapas, proveedores de IA, modelos
  entrenados, almacenamiento de objetos o correo dependen de servicios/configuración externos.
- Los campos sin dato no se deben presentar como mediciones reales; algunos cálculos pueden
  devolver una evaluación preliminar o advertencias.
- Las recomendaciones, resultados de visión, estimaciones de rentabilidad y proyecciones son
  auxiliares y dependen de las fuentes de datos y reglas disponibles.
- La disponibilidad de una API en el backend no implica que exista una pantalla para todos los
  perfiles.
- Los nombres, menús y restricciones se pueden ajustar entre versiones; verificar
  `apps/frontend-web/app.js` (visibilidad por rol) y los controles de autorización del backend
  al preparar una capacitación o despliegue.
- Para instrucciones operativas detalladas por pantalla, consulta
  [Menús y pantallas](../architecture/Documento_Menus_Pantallas_AgroIA.md). Para lógica de
  recomendaciones, persistencia e integración técnica, consulta
  [Documento funcional-técnico](../architecture/Documento_Funcional_Tecnico_AgroIA.md).
