# RNF-009: No Alucinación del Sistema IA

**Tipo:** Requerimiento no funcional
**Categoría:** Calidad / Confiabilidad de IA
**Fuente:** RFP-AgroInteligente-Colombia.md — Secciones 5.10, 5.13, 9

## Descripción
El sistema de IA (tanto el motor predictivo como el agente conversacional) debe cumplir con un principio fundamental de **no alucinación**: nunca debe inventar información, generar datos falsos o hacer afirmaciones sin respaldo en los datos disponibles. Específicamente:

- Si el sistema no tiene evidencia o datos suficientes para generar una recomendación con un nivel de confianza aceptable, debe indicarlo explícitamente: "No hay datos suficientes para determinar..." o "Se requiere información adicional sobre...".
- Toda recomendación debe estar basada en: datos reales del sensor, reglas agronómicas verificables o evidencia documentada en la base de conocimiento del RAG.
- El agente conversacional (RAG) debe responder únicamente con información contenida en los documentos indexados. Si una pregunta está fuera de su dominio de conocimiento, debe indicarlo claramente sin intentar responder.
- Las fuentes de cada afirmación deben ser trazables (cita al documento o regla que la respalda).

## Criterio medible / restricción concreta
- Tasa de alucinación (afirmaciones no respaldadas) debe ser < 1% en evaluaciones de calidad.
- No especificados en el RFP — definir: protocolo de evaluación de alucinaciones (revisión manual por agrónomos expertos), umbral de confianza mínimo para mostrar una recomendación, mecanismo de reporte de respuestas incorrectas por parte de usuarios.

## Impacto en la arquitectura
- El RAG debe configurarse con parámetros conservadores (top-k bajo, threshold de similitud alto) para limitar la generación a documentos relevantes.
- Implementar un "circuito de verificación" que valide las salidas del LLM contra las reglas del sistema experto antes de mostrarlas al usuario.
- Sistema de feedback loop para que técnicos agrónomos puedan marcar recomendaciones incorrectas.
- Logging detallado de cada respuesta del agente IA para auditoría posterior.

## Notas del analista
- La no alucinación es el requisito de calidad más importante para la credibilidad del sistema. Una sola recomendación incorrecta (ej. sugerir un fertilizante equivocado) puede dañar un cultivo y la confianza del agricultor.
- La arquitectura RAG reduce significativamente el riesgo de alucinación comparado con un LLM sin acceso a documentos, pero no lo elimina por completo. El sistema experto basado en reglas actúa como una segunda capa de seguridad.
- Las pruebas de este requisito deben ser realizadas por ingenieros agrónomos reales (del Comité de Cafeteros o Cenicafé) durante el piloto.
