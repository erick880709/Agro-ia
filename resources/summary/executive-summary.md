# Resumen Ejecutivo — RFP-AGROIA-001: Interacción por voz en el Asesor agronómico

**Cliente:** Equipo AGROINTELIGENTE COLOMBIA
**Fecha del documento:** 19 de octubre de 2026
**Documento fuente:** `context/RFP-AGROIA-001_Interaccion_por_voz_Asesor_agronomico.md`

## Objetivo y alcance del proyecto
Evolucionar el Asesor agronómico (chat de reportes) de AgroIA para que productores y técnicos puedan dictar consultas en español desde computadores y teléfonos móviles. La solución debe transcribir la voz, mostrar el texto para revisión y edición, y enviar la consulta confirmada al servicio de chat existente conservando el contexto de la finca y del reporte seleccionados. La primera fase mantiene las respuestas del asistente en texto y no modifica el agente ni sus reglas agronómicas.

Quedan fuera de Fase 1 la respuesta hablada, la conversación continua o manos libres, la personalización de voz, otros idiomas y una aplicación móvil nativa. Estas capacidades podrán evaluarse en Fase 2 con base en el uso real.

## Plazos
Cronograma sugerido, sujeto al plan del oferente:
- Confirmación de arquitectura y alternativa de transcripción: 2–3 días.
- Diseño de interfaz y estados: 2–3 días.
- Implementación e integración: 1–2 semanas.
- Pruebas, ajustes y documentación: 1 semana.
- Despliegue y seguimiento: 1 semana.

## Presupuesto / modelo de contratación
No se fija presupuesto ni modelo contractual. Se solicita estimar costos de implementación y operación, incluyendo costo por uso y límites si se emplea un servicio de pago. La expectativa para Fase 1 es no incurrir en un costo fijo relevante.

## Criterios de evaluación de la propuesta
- Adecuación técnica y compatibilidad con la arquitectura existente: 30%.
- Calidad de experiencia de usuario y manejo de errores: 20%.
- Privacidad, seguridad y cumplimiento normativo: 15%.
- Costo total de implementación y operación: 15%.
- Experiencia y equipo: 10%.
- Plan de pruebas, documentación y soporte: 10%.

## Stakeholders identificados
- Equipo AGROINTELIGENTE COLOMBIA, solicitante.
- Productores / agricultores, usuarios del asesor desde finca o computador.
- Técnicos / extensionistas, usuarios en campo.
- Administrador de AgroIA, responsable potencial de métricas y parámetros.
- Asistente agronómico existente, que procesa consultas y responde en texto.

## Entregables esperados
1. Función de voz implementada y desplegada en el entorno acordado.
2. Código fuente y pruebas automatizadas relevantes.
3. Matriz de pruebas por dispositivo y navegador, con resultados.
4. Actualización de documentos vivos de menús y pantallas, funcional técnico y catálogo funcional; contrato OpenAPI si aplica.
5. Informe de decisión técnica sobre la alternativa de transcripción elegida.
6. Guía breve de uso para usuario final y administrador.

La propuesta también debe incluir enfoque técnico, plan y cronograma, equipo, estrategia de pruebas, tratamiento de privacidad y seguridad, costos, supuestos, exclusiones, riesgos, garantía y soporte.

## Supuestos y restricciones generales
- El Asesor agronómico y su endpoint de chat existen y permanecen estables.
- La intervención debe ser acotada al frontend, con cambios mínimos o nulos en backend.
- La arquitectura descrita actualmente es FastAPI con frontend SPA en JavaScript sin framework, pero debe confirmarse porque una referencia funcional menciona Flask.
- El idioma de la función es español; las pruebas deben contemplar el acento colombiano.
- Los usuarios disponen de un dispositivo con micrófono y un navegador compatible.
- No se almacenan grabaciones; si el procesamiento es en servidor, el audio se descarta al terminar la transcripción.
- El audio transmitido debe viajar por HTTPS; la solución debe cumplir la Ley 1581 de 2012 y las políticas de privacidad de AgroIA.
- Las consultas dictadas deben revisarse y editarse antes de enviarse.

## Glosario
- **Asesor agronómico:** chat de AgroIA que responde preguntas sobre el reporte de suelo y la finca seleccionada.
- **Finca / reporte seleccionado:** contexto agronómico que debe conservar el chat al recibir una consulta dictada.
- **UPRA / Cenicafé / AGROSAVIA:** fuentes o reglas agronómicas indicadas por el RFP como contexto de las respuestas existentes.
- **Web Speech API:** API de reconocimiento de voz disponible en algunos navegadores, alternativa de transcripción evaluada.
- **Enfoque híbrido:** uso de reconocimiento en navegador por defecto y transcripción en servidor como respaldo.

## Resumen cuantitativo de la extracción
- Requerimientos funcionales extraídos: 15
- Requerimientos no funcionales extraídos: 13
- Requisitos técnicos extraídos: 4
- Información de diseño extraída: 1

## Vacíos y riesgos detectados
- Existe una inconsistencia arquitectónica: la descripción actual menciona FastAPI y SPA JavaScript, mientras que otra referencia menciona Flask; confirmar el estado real antes de estimar.
- La alternativa de transcripción (navegador, servidor o híbrida) y el nivel aceptable de precisión en español con vocabulario agronómico no están decididos ni cuantificados.
- No se definen navegadores, versiones y dispositivos que conforman el soporte actual de AgroIA ni la cobertura mínima de pruebas.
- No se cuantifican “pocos segundos”, “precisión aceptable”, “costo fijo relevante” ni umbrales de duración, tamaño y frecuencia.
- Permanecen abiertas la inclusión en Fase 1 de comandos de control y de activación administrativa; además, el RFP presenta como decisión abierta voz hablada aunque la recomienda para una fase futura.
- No se define el volumen esperado de uso ni los criterios de privacidad, retención y anonimización de métricas; confirmar también el aviso al usuario y el tratamiento de terceros.
