# RD-008: Diseño de interacción por voz en el chat

**Tipo:** Información de diseño
**Fuente:** RFP-AGROIA-001 — Secciones 3, 4.1, 6, 7.1 y 8

## Descripción
La interacción por voz se incorpora al chat existente mediante un botón de micrófono junto al campo de texto. El flujo previsto es: solicitar permiso al activar la función; indicar que escucha y que la grabación está activa; detener por acción del usuario o silencio; mostrar procesamiento; colocar la transcripción en el campo para revisión y edición; y esperar una acción explícita de envío. Los estados de error deben orientar al usuario y dejar disponible la escritura.

## Elementos de referencia
- Estados de interfaz: inactivo, grabando, procesando y error.
- Control: botón de micrófono junto al campo de entrada.
- Durante la grabación: indicador visual del nivel de audio y señal de estado no dependiente solo del color.
- Mensajes: ayuda para permisos denegados, falta de conectividad, falta de soporte y error de transcripción.
- No se adjuntan wireframes ni mockups; el diseño detallado queda para la fase de interfaz.

## Notas del analista
El flujo de voz es de dictado con respuesta escrita; no incluye conversación continua ni respuesta hablada del asistente. El RFP deja abierta la decisión de incluir los comandos de control y la opción de voz hablada corresponde a una fase posterior.
