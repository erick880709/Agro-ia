# RFP-AGROIA-001 — Interacción por voz en el Asesor agronómico (chat de reportes)

**Proyecto:** AGROINTELIGENTE COLOMBIA / AgroIA · **Módulo:** Reportes → Asesor agronómico (chat) · **Tipo:** Mejora funcional · **Versión:** 1.0 (borrador) · **Fecha:** 19 de octubre de 2026

## 1. Información general

| Campo | Detalle |
|---|---|
| Identificador | RFP-AGROIA-001 (referencia funcional: RF-AGROIA-001) |
| Solicitante | Equipo AGROINTELIGENTE COLOMBIA |
| Sistema afectado | AgroIA (SPA web + backend de API + asistente agronómico existente) |
| Naturaleza del cambio | Evolutivo sobre una aplicación en producción; no se reescribe el agente |
| Entregable principal | Captura de voz en el chat, transcripción a texto en español, revisión/edición y envío al asistente actual |

## 2. Antecedentes

AgroIA incluye en la pantalla de reportes el **Asesor agronómico (chat)**, donde el usuario selecciona una finca y conversa con un experto virtual sobre su reporte de suelo: cómo abonar, qué sembrar, qué significa cada medición y qué hacer en el terreno. La pantalla ofrece consultas rápidas (“¿Cómo está mi suelo?”, “¿Qué abono debo aplicar?”, “¿Qué me conviene sembrar?”, “Explícame el reporte”), un campo de texto, un botón **Enviar** y la nota de que las respuestas se basan en la lectura de suelo y en las reglas UPRA/Cenicafé/AGROSAVIA de la finca seleccionada.

Hoy toda interacción exige escribir. Para productores y técnicos de campo, que con frecuencia usan el teléfono móvil, con guantes, a la intemperie o con baja familiaridad con el teclado, esto limita el uso del asesor. Se requiere habilitar el **comando de voz** para que el usuario pueda decirle al asistente qué necesita, sin cambiar la lógica del agente.

## 3. Objetivo

**Objetivo general.** Permitir que el usuario interactúe con el Asesor agronómico mediante voz, además de la escritura, de forma natural, accesible y sencilla.

**Objetivos específicos**

- Incorporar un botón de micrófono funcional junto al campo de texto del chat.
- Convertir la voz en texto en español (con vocabulario agronómico colombiano) y mostrarla en el campo de entrada.
- Permitir revisar, corregir y confirmar la consulta antes de enviarla.
- Reutilizar el servicio de chat existente, conservando el contexto de la finca/reporte seleccionado.
- Garantizar que, si la voz falla, el usuario pueda seguir escribiendo sin fricción.

## 4. Alcance

### 4.1 Dentro del alcance (Fase 1)

- Botón de micrófono con estados visibles: inactivo, grabando, procesando, error.
- Gestión de permisos del micrófono y de sus mensajes de ayuda.
- Transcripción de voz a texto en español.
- Inserción de la transcripción en el campo de entrada para revisión y edición.
- Envío al asistente actual mediante el endpoint de chat existente.
- Comandos de voz de control básicos del chat (ver RF-08).
- Compatibilidad con computadores y teléfonos móviles en los navegadores soportados por AgroIA.
- Pruebas, documentación y actualización de los documentos vivos de arquitectura y de menús/pantallas.

### 4.2 Fuera del alcance

- Respuesta hablada del asistente (texto a voz).
- Conversación de voz en tiempo real o manos libres continuo.
- Personalización de voces de salida.
- Cambios al motor de reglas, al agente o a la lógica de recomendaciones.
- Soporte de otros idiomas distintos del español.
- Aplicación móvil nativa.

Estas capacidades se consideran **Fase 2** y se evaluarán con base en el uso real de la Fase 1.

## 5. Actores

| Actor | Descripción |
|---|---|
| Productor / agricultor | Consulta su reporte desde el teléfono o el computador |
| Técnico / extensionista | Usa el chat en campo para orientar decisiones |
| Administrador | Consulta métricas de uso y configura parámetros de la función |
| Asistente agronómico | Servicio existente que procesa la pregunta y responde por texto |

## 6. Flujo funcional esperado

1. El usuario abre un reporte, selecciona la finca y entra al Asesor agronómico.
2. Pulsa el micrófono; si es la primera vez, el navegador solicita permiso.
3. La interfaz indica “Escuchando…” y muestra que la grabación está activa.
4. El usuario habla con naturalidad. Ejemplo: “¿Qué significa que mi suelo tenga poca materia orgánica y cómo la mejoro?”.
5. Al detener la grabación (manualmente o por silencio), la interfaz indica “Procesando…”.
6. La transcripción aparece en el campo de texto; el usuario puede editarla.
7. El usuario pulsa **Enviar** (o dice “enviar”) y el asistente responde dentro del chat, con el contexto de la finca seleccionada.
8. Ante permiso denegado, falta de conexión o error de transcripción, se muestra un mensaje claro y el campo de texto sigue disponible.

## 7. Requerimientos funcionales

Prioridad: **M** = Mandatorio, **D** = Deseable.

| ID | Requerimiento | Prioridad |
|---|---|---|
| RF-01 | Mostrar un botón de micrófono identificable junto al campo de texto del chat | M |
| RF-02 | Permitir iniciar y detener la grabación de voz | M |
| RF-03 | Solicitar el permiso de micrófono solo cuando el usuario lo active y explicar cómo habilitarlo si fue denegado | M |
| RF-04 | Transcribir la voz a texto en español | M |
| RF-05 | Insertar la transcripción en el campo de entrada, editable, sin enviarla automáticamente | M |
| RF-06 | Enviar la consulta al servicio de chat existente, sin duplicar la lógica del agente | M |
| RF-07 | Conservar el contexto de la finca/reporte seleccionado en la consulta por voz | M |
| RF-08 | Soportar comandos de voz de control: “enviar”, “borrar”, “cancelar” y “repetir” (volver a dictar) | D |
| RF-09 | Informar el estado: grabando, procesando, error; incluir indicador visual de nivel de audio | M |
| RF-10 | Mantener sin cambios el flujo de escritura y las consultas rápidas actuales | M |
| RF-11 | Degradar con elegancia cuando el navegador no soporte captura de voz (ocultar o deshabilitar el botón con mensaje) | M |
| RF-12 | Definir un tiempo máximo de grabación por consulta (parametrizable) | M |
| RF-13 | Reconocer términos agronómicos comunes (materia orgánica, pH, fósforo, nitrógeno, cultivares, nombres de los cultivos del catálogo) | D |
| RF-14 | Registrar métricas de uso sin audio: cantidad de consultas por voz, errores y duración | D |
| RF-15 | Permitir al administrador activar o desactivar la función desde Administración → Parámetros | D |

### 7.1 Comandos de voz de control (RF-08)

La función de “indicarle qué hacer” se limita en Fase 1 a controlar el propio chat. Las instrucciones de contenido (“¿qué abono debo aplicar?”) siguen siendo preguntas al asistente existente. Los comandos de control se reconocen únicamente cuando se pronuncian solos, para evitar confundirlos con parte de una pregunta.

| Comando | Acción |
|---|---|
| “Enviar” | Envía el texto actual del campo |
| “Borrar” / “Cancelar” | Limpia el campo de entrada |
| “Repetir” | Descarta la transcripción y reinicia la grabación |

## 8. Requerimientos no funcionales

| Categoría | Requerimiento |
|---|---|
| Usabilidad | Interfaz apta para móvil; botón con tamaño táctil adecuado; textos en español claro |
| Accesibilidad | Etiquetas accesibles (aria) en el botón y los estados; no depender solo del color para indicar grabación |
| Rendimiento | Transcripción visible en un tiempo objetivo de pocos segundos tras finalizar el dictado (valor a acordar en la propuesta) |
| Disponibilidad | La caída del servicio de voz no debe afectar el chat de texto |
| Compatibilidad | Navegadores y dispositivos soportados por AgroIA; se debe entregar una matriz de pruebas |
| Conectividad | Mensaje claro ante conectividad baja o nula; considerar zonas rurales con señal limitada |
| Costos | Sin costo fijo relevante en Fase 1; si se usa un servicio de pago, estimar costo por minuto y límites de uso |
| Mantenibilidad | Código modular, sin valores de negocio fijos; parámetros administrables |

## 9. Consideraciones técnicas

El backend actual del proyecto está basado en FastAPI con frontend SPA en JavaScript sin framework; el requerimiento funcional original menciona Flask, por lo que el oferente debe **confirmar la arquitectura vigente** antes de proponer. La solución debe ser un cambio acotado del frontend, con cambios mínimos o nulos en backend.

### 9.1 Alternativas de transcripción a evaluar

| Alternativa | Ventajas | Riesgos / limitaciones |
|---|---|---|
| A. API de reconocimiento de voz del navegador (Web Speech API) | Implementación rápida, sin costo propio, sin infraestructura nueva | Soporte desigual entre navegadores, en algunos casos el audio se procesa en servicios del proveedor del navegador, requiere conexión |
| B. Transcripción en servidor (endpoint que recibe audio y devuelve texto) | Comportamiento uniforme, control de idioma y vocabulario, mejor trazabilidad | Costo por uso, latencia, manejo seguro de audio, nuevo endpoint a mantener |
| C. Enfoque híbrido (A por defecto, B como respaldo) | Cobertura amplia con costo contenido | Mayor complejidad de implementación y pruebas |

El oferente debe justificar su elección con base en compatibilidad, precisión en español, límites de uso, costo y privacidad. **Recomendación del solicitante:** iniciar con A o C y validar con usuarios reales antes de invertir en B.

### 9.2 Lineamientos de integración

- Reutilizar el endpoint de chat existente; la consulta por voz llega como texto, indistinguible de una escrita.
- Si se crea un endpoint de transcripción, debe exigir autenticación, limitar tamaño y duración del audio y aplicar tasa de peticiones.
- No modificar el agente ni las reglas UPRA/Cenicafé/AGROSAVIA.
- Cualquier parámetro (duración máxima, activación, idioma) debe ser administrable, no fijo en el código.

## 10. Seguridad y privacidad

- No almacenar grabaciones; si el procesamiento es en servidor, descartar el audio al terminar la transcripción.
- Transmitir cualquier audio solo por canal cifrado (HTTPS).
- Informar al usuario, de forma breve, que su voz se convierte en texto y si un tercero participa en el procesamiento.
- Cumplir la normativa colombiana de protección de datos personales (Ley 1581 de 2012) y las políticas de privacidad de AgroIA; la voz puede constituir un dato personal.
- No registrar el contenido de las consultas más allá de lo que el chat actual ya registra.
- Prevenir abuso mediante límites de duración, tamaño y frecuencia.

## 11. Criterios de aceptación

- [ ] El chat conserva intacto su funcionamiento de escritura y las consultas rápidas.
- [ ] Se muestra un botón de micrófono claramente identificable.
- [ ] El usuario puede iniciar y detener la grabación.
- [ ] La aplicación solicita permiso del micrófono y orienta al usuario si fue denegado.
- [ ] La voz se convierte a texto en español con precisión aceptable en pruebas con vocabulario agronómico.
- [ ] El usuario puede revisar y editar la transcripción antes de enviarla.
- [ ] El envío usa el servicio de chat existente, sin duplicar la lógica del agente.
- [ ] La consulta conserva el contexto de la finca/reporte seleccionado.
- [ ] Ante permiso denegado, ausencia de conexión o error de transcripción, el usuario puede seguir escribiendo.
- [ ] La interfaz informa cuándo está grabando, procesando o ha ocurrido un error.
- [ ] La función se valida en los dispositivos y navegadores soportados, con matriz de pruebas documentada.
- [ ] No se almacenan grabaciones de audio.

## 12. Supuestos y restricciones

- El Asesor agronómico y su endpoint de chat existen y permanecen estables.
- Los usuarios cuentan con un dispositivo con micrófono y un navegador compatible.
- La primera versión entrega respuestas solo en texto.
- El idioma de la función es el español; el acento colombiano debe estar contemplado en las pruebas.
- La conectividad en campo puede ser limitada, por lo que se espera tolerancia a fallos.

## 13. Riesgos

| Riesgo | Impacto | Mitigación |
|---|---|---|
| Soporte desigual de reconocimiento de voz entre navegadores | Alto | Detección de capacidad, enfoque híbrido y mensaje de respaldo |
| Baja precisión con términos agronómicos y ruido de campo | Medio | Revisión editable obligatoria, pruebas con audios reales, vocabulario de apoyo |
| Costo variable si se usa servicio de pago | Medio | Límites de duración y uso, activación parametrizable |
| Confusión entre comandos de control y contenido de la pregunta | Medio | Reconocer comandos solo cuando se dicen solos; confirmación visual |
| Privacidad del audio | Alto | Sin almacenamiento, transparencia al usuario, cumplimiento de Ley 1581 |
| Permisos denegados por el usuario | Bajo | Guía visual para habilitarlos y alternativa de escritura |

## 14. Entregables

1. Función de voz implementada y desplegada en el entorno acordado.
2. Código fuente con pruebas automatizadas relevantes.
3. Matriz de pruebas por dispositivo y navegador, con resultados.
4. Actualización de los documentos vivos: menús y pantallas, funcional técnico, catálogo funcional y, si aplica, contrato OpenAPI.
5. Informe de decisión técnica sobre la alternativa de transcripción elegida.
6. Guía breve de uso para el usuario final y para el administrador.

## 15. Cronograma sugerido

| Fase | Actividad | Duración estimada |
|---|---|---|
| 0 | Confirmación de arquitectura y alternativa de transcripción | 2 a 3 días |
| 1 | Diseño de interfaz y estados del micrófono | 2 a 3 días |
| 2 | Implementación de captura, transcripción e integración con el chat | 1 a 2 semanas |
| 3 | Pruebas en dispositivos, ajustes y documentación | 1 semana |
| 4 | Despliegue y seguimiento de uso | 1 semana |

Los tiempos son referenciales; el oferente debe presentar su propio plan.

## 16. Contenido de la propuesta

La propuesta debe incluir:

- Comprensión del requerimiento y enfoque técnico propuesto, con la alternativa de transcripción justificada.
- Plan de trabajo y cronograma.
- Equipo asignado y experiencia en proyectos similares (voz, frontend web, integraciones de IA).
- Estrategia de pruebas y matriz de compatibilidad.
- Tratamiento de privacidad y seguridad del audio.
- Estimación de costos de implementación y de operación (costo por uso, si aplica).
- Supuestos, exclusiones y riesgos identificados.
- Condiciones de garantía y soporte posterior al despliegue.

## 17. Criterios de evaluación

| Criterio | Peso sugerido |
|---|---|
| Adecuación técnica y compatibilidad con la arquitectura existente | 30% |
| Calidad de la experiencia de usuario y manejo de errores | 20% |
| Privacidad, seguridad y cumplimiento normativo | 15% |
| Costo total (implementación y operación) | 15% |
| Experiencia y equipo | 10% |
| Plan de pruebas, documentación y soporte | 10% |

## 18. Decisiones abiertas

1. **Experiencia de la primera versión:** Opción A (hablar y enviar, respuesta en texto) u Opción B (conversación por voz con respuesta hablada). Se recomienda la Opción A.
2. **Plataformas:** solo aplicación web de escritorio y móvil, o también otros canales.
3. **Alternativa de transcripción:** navegador, servidor o híbrida.
4. **Comandos de voz de control:** confirmar si entran en Fase 1 (RF-08) o pasan a Fase 2.
5. **Métricas y administración:** definir si la activación desde Administración → Parámetros es requisito de Fase 1.
