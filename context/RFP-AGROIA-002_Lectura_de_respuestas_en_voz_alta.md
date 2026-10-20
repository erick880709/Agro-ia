# RFP-AGROIA-002 — Lectura en voz alta de las respuestas del Asesor agronómico (con voz femenina, masculina y voz personalizada)

**Proyecto:** AGROINTELIGENTE COLOMBIA / AgroIA · **Módulo:** Reportes → Asesor agronómico (chat) · **Tipo:** Mejora funcional · **Versión:** 1.0 (borrador) · **Fecha:** 19 de octubre de 2026

**Relación con otros documentos:** complementa el RFP-AGROIA-001 (entrada por voz). Juntos habilitan una experiencia de conversación hablada: el usuario dicta (001) y la aplicación responde en voz alta (002).

## 1. Información general

| Campo | Detalle |
|---|---|
| Identificador | RFP-AGROIA-002 |
| Solicitante | Equipo AGROINTELIGENTE COLOMBIA |
| Sistema afectado | AgroIA (SPA web + backend de API + asistente agronómico existente) |
| Naturaleza del cambio | Evolutivo sobre una aplicación en producción; no se modifica el agente ni sus reglas |
| Entregable principal | Opción para que la aplicación lea en voz alta las respuestas del chat, con selección de voz femenina o masculina, y como valor agregado, voz personalizada grabada por el usuario |
| Restricción económica | Priorizar APIs y componentes gratuitos o de código abierto |

## 2. Antecedentes

El **Asesor agronómico (chat)** de AgroIA responde por texto sobre el reporte de suelo de la finca seleccionada: cómo abonar, qué sembrar, qué significa cada medición y qué hacer en el terreno. Muchos usuarios son productores y técnicos que trabajan en campo, con las manos ocupadas, bajo el sol o con poca costumbre de leer textos largos en pantalla.

Escuchar la respuesta mejora la accesibilidad y la comprensión, y es el complemento natural de la entrada por voz (RFP-AGROIA-001). Además, permitir elegir una voz (femenina o masculina) y, como plus, usar la propia voz del usuario, hace la experiencia más cercana y personal.

## 3. Objetivo

**Objetivo general.** Permitir que el usuario escuche las respuestas del Asesor agronómico leídas en voz alta, con control total para encender o apagar la función cuando quiera.

**Objetivos específicos**

- Ofrecer un interruptor claro para activar o desactivar la lectura de respuestas, recordando la preferencia del usuario.
- Permitir elegir entre una voz femenina y una masculina en español.
- Controlar la reproducción: reproducir, pausar, detener y repetir una respuesta, y ajustar la velocidad.
- (Plus) Permitir que el usuario grabe su propia voz para que la aplicación le lea las respuestas con ella.
- Utilizar APIs gratuitas o de código abierto, con un plan de contingencia ante agotamiento de cuotas.

## 4. Alcance

### 4.1 Dentro del alcance

**Fase 1 — Lectura con voces predefinidas (obligatoria)**

- Interruptor “Leer respuestas en voz alta” en el chat y en las preferencias del usuario.
- Selector de voz femenina o masculina, con botón de prueba (“Escuchar muestra”).
- Controles de reproducción por respuesta y control de velocidad.
- Lectura automática de las nuevas respuestas cuando la función está activa; lectura manual de cualquier respuesta con un botón de altavoz.
- Preparación del texto para lectura (omitir símbolos, tablas y marcas de formato; leer números y unidades agronómicas de forma natural).
- Plan de respaldo entre motores de voz.

**Fase 2 — Voz personalizada (plus)**

- Flujo guiado para que el usuario grabe una muestra de su voz.
- Consentimiento explícito y verificación de que la voz es la del propio usuario.
- Generación de una voz sintética a partir de la muestra y su uso en la lectura de respuestas.
- Posibilidad de previsualizar, regrabar, desactivar y eliminar la voz personalizada.

### 4.2 Fuera del alcance

- Cambios al agente, a las reglas UPRA/Cenicafé/AGROSAVIA o al contenido de las respuestas.
- Conversación de voz en tiempo real con interrupciones (se evaluará en una fase posterior).
- Idiomas distintos del español.
- Clonación de voces de terceros o de personas públicas.
- Aplicación móvil nativa.

## 5. Actores

| Actor | Descripción |
|---|---|
| Productor / agricultor | Escucha respuestas en campo; elige voz y activa o desactiva la lectura |
| Técnico / extensionista | Usa la lectura para consultar y orientar sin mirar la pantalla |
| Administrador | Configura motores de voz, límites y activación general de la función |
| Asistente agronómico | Genera la respuesta de texto que luego se convierte en audio |

## 6. Flujo funcional esperado

### 6.1 Lectura con voz predefinida

1. El usuario activa **“Leer respuestas en voz alta”** desde el chat o sus preferencias.
2. Elige **Voz femenina** o **Voz masculina** y pulsa “Escuchar muestra” para probarla.
3. Formula una consulta (por texto o por voz).
4. El asistente responde en texto, como hoy.
5. La aplicación convierte la respuesta en audio y la reproduce; el usuario puede pausar, detener, repetir o cambiar la velocidad.
6. El usuario puede apagar la función en cualquier momento; la lectura en curso se detiene de inmediato.
7. Si el motor de voz no está disponible, la respuesta de texto se muestra normalmente y se informa el problema con un mensaje breve.

### 6.2 Voz personalizada (plus)

1. En preferencias, el usuario elige **“Crear mi voz”**.
2. La aplicación explica qué se grabará, para qué se usa y por cuánto tiempo se conserva, y solicita consentimiento explícito.
3. El usuario graba una muestra guiada leyendo textos propuestos, con indicadores de calidad (ruido, volumen, duración).
4. La aplicación procesa la muestra y habilita una prueba de la voz resultante.
5. Si el usuario está conforme, activa **“Mi voz”** como tercera opción junto a femenina y masculina.
6. El usuario puede regrabar, desactivar o **eliminar** su voz en cualquier momento.

## 7. Requerimientos funcionales

Prioridad: **M** = Mandatorio, **D** = Deseable, **P** = Plus (Fase 2).

| ID | Requerimiento | Prioridad |
|---|---|---|
| RF-01 | Interruptor visible para activar o desactivar la lectura de respuestas, con estado persistente por usuario | M |
| RF-02 | Selector de voz femenina o masculina en español | M |
| RF-03 | Botón “Escuchar muestra” para probar la voz antes de elegirla | M |
| RF-04 | Lectura automática de nuevas respuestas cuando la función está activa | M |
| RF-05 | Botón de altavoz en cada respuesta para leerla manualmente, incluso con la función apagada | D |
| RF-06 | Controles de reproducción: reproducir, pausar, detener y repetir | M |
| RF-07 | Control de velocidad de lectura (por ejemplo 0,75x, 1x, 1,25x, 1,5x) | D |
| RF-08 | Detener automáticamente la lectura al apagar la función, enviar una nueva consulta o salir del chat | M |
| RF-09 | Limpiar el texto antes de leerlo: omitir símbolos, formato, enlaces y tablas; leer unidades (ppm, meq/100 g, %, kg/ha) de forma natural | M |
| RF-10 | Mantener sin cambios la respuesta escrita y el flujo actual del chat | M |
| RF-11 | Conmutar a un motor de respaldo si el motor principal falla o agota su cuota | M |
| RF-12 | Informar el estado: preparando audio, reproduciendo, error | M |
| RF-13 | Respetar la preferencia de voz y activación en todos los dispositivos del usuario | D |
| RF-14 | Flujo guiado de grabación de la voz del usuario con indicadores de calidad | P |
| RF-15 | Consentimiento explícito previo a la grabación y verificación de que la voz pertenece al usuario | P |
| RF-16 | Previsualizar, regrabar, desactivar y eliminar la voz personalizada | P |
| RF-17 | Mostrar “Mi voz” como opción de voz solo cuando exista y esté activa | P |
| RF-18 | Permitir al administrador activar o desactivar la función y la voz personalizada, y fijar límites de uso, desde Administración → Parámetros | D |
| RF-19 | Registrar métricas de uso sin guardar contenido de audio: activaciones, voz elegida, errores, caracteres leídos | D |

## 8. Requerimientos no funcionales

| Categoría | Requerimiento |
|---|---|
| Usabilidad | Interruptor y controles con tamaño táctil adecuado; estado siempre visible; textos en español claro |
| Accesibilidad | Etiquetas accesibles en controles; operación por teclado; no depender solo del color |
| Rendimiento | Inicio de la reproducción en pocos segundos tras recibir la respuesta (valor a acordar); lectura por fragmentos para respuestas largas |
| Disponibilidad | La falla de la lectura no debe afectar el chat de texto |
| Compatibilidad | Navegadores y dispositivos soportados por AgroIA; matriz de pruebas obligatoria |
| Conectividad | Tolerancia a señal limitada en zonas rurales; preferir motores que funcionen sin conexión o con poco ancho de banda |
| Costos | Costo operativo cercano a cero en Fase 1; estimación explícita para Fase 2 |
| Calidad de audio | Voces naturales y comprensibles con acento neutro o latinoamericano |
| Mantenibilidad | Motores de voz intercambiables detrás de una interfaz común; parámetros administrables |

## 9. APIs y motores gratuitos evaluados

Los datos provienen de fuentes públicas consultadas el 19 de octubre de 2026. Las condiciones gratuitas cambian con frecuencia, por lo que **el oferente debe verificar límites, licencias y precios vigentes antes de comprometerse**.

### 9.1 Motores para voces predefinidas (femenina y masculina)

| Opción | Costo / cuota gratuita | Voces en español | Ventajas | Riesgos / limitaciones |
|---|---|---|---|---|
| **A. API de síntesis de voz del navegador (Web Speech API, `speechSynthesis`)** | Gratis, sin llave ni cuenta | Dependen del navegador y del sistema operativo; hay variantes de es-ES, es-MX y es-US | Sin costo, funciona sin servidor propio y puede operar sin conexión | El estándar no expone género de la voz; la disponibilidad y calidad varían entre dispositivos; hay que identificar voces femeninas y masculinas por nombre o por una lista curada |
| **B. Google Cloud Text-to-Speech** | Capa gratuita mensual recurrente: aprox. 4 millones de caracteres en voces estándar y 1 millón en voces WaveNet | Catálogo amplio con voces femeninas y masculinas definidas explícitamente | Género controlable, buena calidad, cuota mensual que se renueva | Requiere cuenta de facturación y llave de API; sobrepasar la cuota genera cobro |
| **C. Azure AI Speech (voces neuronales)** | Nivel gratuito: aprox. 500.000 caracteres mensuales en voces neuronales | Amplio catálogo con voces es-CO, es-MX, es-ES y otras | Voces neuronales con acento latinoamericano, género explícito | Requiere suscripción de Azure y control de cuota |
| **D. Amazon Polly** | Capa gratuita por 12 meses: aprox. 5 millones de caracteres estándar y 1 millón neuronales al mes | Voces en español con género definido | Cuota alta para empezar | La gratuidad es temporal (primer año) |
| **E. Piper (código abierto, autoalojado)** | Gratis; costo de infraestructura propio | Decenas de voces en español (es_ES, es_MX) | Muy liviano, funciona en CPU, sin dependencia de terceros, apto para contingencia | La calidad es menor que la de motores neuronales de nube; hay que alojarlo y mantenerlo |
| **F. Kokoro (Apache 2.0, autoalojado)** | Gratis; costo de infraestructura propio | Incluye español | Calidad alta y licencia permisiva | No permite clonación de voz; el catálogo de voces en español es limitado |

Otras opciones revisadas y **descartadas para Fase 1**: ElevenLabs y Speechify tienen plan gratuito, pero con cuotas pequeñas (alrededor de 10.000 créditos al mes en ElevenLabs y 50.000 caracteres al mes en Speechify) que se agotarían rápido con respuestas largas del asesor.

### 9.2 Motores para voz personalizada (plus)

El hallazgo clave es que **ninguna API en la nube ofrece clonación de voz gratuita con derechos comerciales**. Las rutas viables son autoalojar un modelo abierto o pagar un plan.

| Opción | Costo | Licencia / condiciones | Notas |
|---|---|---|---|
| **G. Chatterbox Multilingual (autoalojado)** | Software gratuito; requiere servidor con GPU (se recomienda NVIDIA con 8 GB o más de VRAM) | MIT, uso comercial permitido | Clonación a partir de una muestra corta, soporta 23 idiomas incluido español, incorpora marca de agua de audio para uso responsable |
| **H. Qwen3-TTS (autoalojado)** | Software gratuito; requiere GPU | Apache 2.0 | Clonación sin entrenamiento previo en 10 idiomas, incluido español; evaluar madurez y costo de operación |
| **I. XTTS-v2 (autoalojado)** | Software gratuito; requiere GPU | Licencia CPML, restringida a uso no comercial | Muy buena calidad de clonación, pero **no apto si AgroIA se usa comercialmente** sin acuerdo aparte |
| **J. ElevenLabs (Instant Voice Cloning)** | No incluido en el plan gratuito; disponible desde el plan Starter (cerca de 5 a 6 USD al mes) | Licencia comercial desde Starter | Alta calidad y simplicidad de integración, pero de pago y con cuota de créditos limitada |

### 9.3 Recomendación del solicitante

1. **Fase 1:** enfoque híbrido con cadena de respaldo. Voz del navegador (A) como opción inicial sin costo, con una lista curada de voces femeninas y masculinas; una API en la nube con capa gratuita recurrente (B o C) como motor consistente cuando se requiera calidad y género garantizados; Piper (E) como contingencia autoalojada.
2. **Fase 2 (plus):** evaluar Chatterbox Multilingual (G) por su licencia MIT y soporte de español, validando primero con una prueba de concepto el costo de GPU y la calidad con acentos colombianos. Si el costo de GPU no se justifica, se puede evaluar J como opción de pago bajo.
3. No usar XTTS-v2 (I) en un producto comercial sin resolver su licencia.

## 10. Consideraciones técnicas

- Definir una **interfaz común de síntesis** (por ejemplo, un servicio de voz con una operación “texto → audio”) para intercambiar motores sin tocar el chat.
- Reutilizar la respuesta de texto existente; no modificar el agente ni su endpoint de chat.
- **Control de cuota:** guardar en caché el audio de respuestas repetidas por voz y fragmento (sin datos personales), limitar la longitud leída (por ejemplo, resumir o leer solo las primeras secciones con opción “seguir leyendo”), y aplicar límites por usuario.
- **Preprocesamiento del texto:** eliminar formato Markdown, expandir abreviaturas y unidades, y dividir en frases para iniciar la reproducción antes de terminar la síntesis completa.
- Si la voz se genera en servidor, exponer un endpoint autenticado con límite de tamaño, tasa de peticiones y tiempo de espera; el audio se devuelve por transmisión (streaming) o en fragmentos.
- La preferencia de activación, la voz elegida y la velocidad se guardan en el perfil del usuario.
- Para la voz personalizada: procesamiento asíncrono con estado visible (“procesando tu voz”), almacenamiento cifrado de la muestra o de la representación de voz, y eliminación efectiva al borrar.
- Documentar cómo alojar y escalar el servicio de GPU, o justificar el uso de un servicio externo, junto con una estimación de costo mensual.

## 11. Seguridad y privacidad

- **Consentimiento explícito e informado** antes de grabar: finalidad, quién procesa la voz, cuánto tiempo se conserva y cómo eliminarla.
- La voz es un dato personal y puede considerarse **dato biométrico sensible** bajo la normativa colombiana de protección de datos (Ley 1581 de 2012); el oferente debe tratar este punto con asesoría jurídica y reflejarlo en la política de privacidad de AgroIA.
- Permitir solo la clonación de la **propia voz del usuario**: incluir una frase de verificación leída en el momento de la grabación y prohibir la carga de audios de terceros.
- Prevenir suplantación: no compartir voces entre usuarios, no exponer la voz personalizada por API pública, aplicar marcas de agua cuando el modelo lo soporte.
- Cifrar muestras y voces en reposo y en tránsito; eliminarlas por completo cuando el usuario lo solicite o cierre su cuenta.
- No guardar el audio de las respuestas leídas más allá de la caché técnica estrictamente necesaria, y sin datos personales.
- Aplicar límites de uso y de tamaño para evitar abuso y costos inesperados.

## 12. Criterios de aceptación

**Fase 1**

- [ ] El usuario puede activar y desactivar la lectura de respuestas, y la preferencia se conserva entre sesiones.
- [ ] Al apagar la función, la lectura en curso se detiene de inmediato.
- [ ] El usuario puede elegir voz femenina o masculina y probarla antes de usarla.
- [ ] Las respuestas nuevas se leen automáticamente cuando la función está activa.
- [ ] El usuario puede pausar, detener y repetir la lectura, y cambiar la velocidad.
- [ ] El texto se lee de forma natural, sin pronunciar símbolos ni formato, y con unidades agronómicas correctas.
- [ ] Si un motor de voz falla o agota su cuota, el sistema cambia al respaldo o informa el problema sin afectar el chat de texto.
- [ ] La respuesta escrita y el funcionamiento actual del chat permanecen sin cambios.
- [ ] La función se valida en los dispositivos y navegadores soportados, con matriz de pruebas documentada.
- [ ] El costo operativo de Fase 1 se mantiene dentro de las capas gratuitas definidas, con monitoreo de consumo.

**Fase 2 (plus)**

- [ ] El usuario puede grabar su voz con orientación sobre calidad y duración.
- [ ] La grabación exige consentimiento explícito y verificación de que la voz es la del propio usuario.
- [ ] El usuario puede previsualizar, regrabar, desactivar y eliminar su voz.
- [ ] “Mi voz” aparece como opción solo cuando existe y está activa.
- [ ] Al eliminar la voz, la muestra y la representación de voz se borran por completo.
- [ ] La inteligibilidad y el parecido de la voz generada se validan con un grupo de usuarios de prueba.

## 13. Supuestos y restricciones

- El Asesor agronómico y su endpoint de chat existen y permanecen estables.
- Los usuarios cuentan con altavoz o audífonos y un navegador compatible.
- Las voces predefinidas cubren español neutro o latinoamericano.
- La voz personalizada es una funcionalidad opcional y puede entrar en una fase posterior si el costo de GPU o la licencia no se justifican.
- Las capas gratuitas de terceros pueden cambiar sin previo aviso.

## 14. Riesgos

| Riesgo | Impacto | Mitigación |
|---|---|---|
| Las voces del navegador varían por dispositivo y no exponen género | Medio | Lista curada de voces por plataforma, motor en la nube como respaldo |
| Agotamiento de la cuota gratuita | Alto | Caché, límites de lectura por usuario, cadena de respaldo, monitoreo y alertas |
| Cambio de condiciones o precios de las APIs gratuitas | Medio | Interfaz común intercambiable, contingencia autoalojada con Piper |
| Costo y operación de GPU para voz personalizada | Alto | Prueba de concepto previa, fase separada, alternativa de pago bajo |
| Licencia no apta para uso comercial (por ejemplo, XTTS-v2) | Alto | Seleccionar modelos con licencias MIT o Apache 2.0 y validación legal |
| Suplantación o uso indebido de voces | Alto | Verificación de voz propia, consentimiento, aislamiento por usuario, marca de agua |
| Datos biométricos y cumplimiento normativo | Alto | Consentimiento, cifrado, eliminación efectiva, asesoría jurídica |
| Mala pronunciación de términos técnicos | Medio | Diccionario de pronunciación y preprocesamiento de unidades |
| Audio largo que fatiga o retrasa la respuesta | Medio | Lectura por fragmentos, opción de lectura parcial y control de velocidad |

## 15. Entregables

1. Función de lectura de respuestas implementada y desplegada en el entorno acordado.
2. Servicio de voz con interfaz común de motores intercambiables y cadena de respaldo.
3. Selector de voz femenina y masculina, con muestra y controles de reproducción.
4. (Plus) Flujo de grabación y gestión de voz personalizada, con servicio de síntesis desplegado.
5. Código fuente con pruebas automatizadas relevantes.
6. Matriz de pruebas por dispositivo y navegador, con resultados.
7. Informe de decisión técnica con comparación de motores, licencias y costos vigentes.
8. Estimación de consumo y costo mensual, con plan de monitoreo de cuotas.
9. Actualización de los documentos vivos: menús y pantallas, funcional técnico, catálogo funcional y, si aplica, contrato OpenAPI.
10. Guía breve de uso para el usuario final y para el administrador.

## 16. Cronograma sugerido

| Fase | Actividad | Duración estimada |
|---|---|---|
| 0 | Confirmación de arquitectura y selección de motores | 3 a 5 días |
| 1 | Diseño de interfaz: interruptor, selector de voz y controles | 3 a 5 días |
| 2 | Implementación de la lectura con voces predefinidas y respaldo | 1 a 2 semanas |
| 3 | Pruebas en dispositivos, ajuste de pronunciación y documentación | 1 semana |
| 4 | Prueba de concepto de voz personalizada (plus) | 1 a 2 semanas |
| 5 | Implementación de voz personalizada, privacidad y pruebas (plus) | 2 a 3 semanas |
| 6 | Despliegue y seguimiento de consumo | 1 semana |

Los tiempos son referenciales; el oferente debe presentar su propio plan. Las fases 4 y 5 son opcionales y pueden contratarse por separado.

## 17. Contenido de la propuesta

La propuesta debe incluir:

- Comprensión del requerimiento y enfoque técnico, con los motores de voz seleccionados y su justificación.
- Verificación de cuotas, licencias y precios vigentes de cada API o modelo propuesto.
- Plan de trabajo y cronograma por fases, con opción de contratar el plus por separado.
- Estrategia de control de cuota y de costos.
- Arquitectura de la voz personalizada y estimación de infraestructura (GPU), o alternativa propuesta.
- Tratamiento de privacidad, consentimiento y datos biométricos.
- Equipo asignado y experiencia en voz, frontend web e integración de IA.
- Estrategia de pruebas y matriz de compatibilidad.
- Estimación de costos de implementación y de operación mensual.
- Supuestos, exclusiones y riesgos.
- Condiciones de garantía y soporte posterior al despliegue.

## 18. Criterios de evaluación

| Criterio | Peso sugerido |
|---|---|
| Adecuación técnica y calidad de la experiencia de voz | 25% |
| Costo total y uso eficiente de capas gratuitas | 20% |
| Privacidad, seguridad y cumplimiento normativo (incluida la voz personalizada) | 20% |
| Resiliencia: respaldo, control de cuota y tolerancia a fallos | 10% |
| Experiencia y equipo | 10% |
| Plan de pruebas, documentación y soporte | 10% |
| Viabilidad de la voz personalizada (plus) | 5% |

## 19. Decisiones abiertas

1. **Motor principal de Fase 1:** voz del navegador, API en la nube con capa gratuita (Google o Azure) o enfoque híbrido. Se recomienda el híbrido.
2. **Voz personalizada:** confirmar si se incluye en la primera entrega o si se difiere a una fase posterior, dado que exige GPU propia o un plan de pago.
3. **Modo de lectura:** lectura completa o parcial con “seguir leyendo”, para controlar cuota y atención del usuario.
4. **Lectura automática por defecto:** si la función se ofrece apagada (recomendado) o encendida para usuarios nuevos.
5. **Uso comercial de AgroIA:** definirlo para descartar o permitir modelos con licencia restringida.
6. **Infraestructura de GPU:** autoalojar, usar un servicio externo o diferir la voz personalizada.
7. **Integración con RFP-AGROIA-001:** definir si ambas funciones se entregan juntas o por separado.
