# RF-013: Recomendaciones Inteligentes de Aptitud del Suelo

**Tipo:** Requerimiento funcional
**Fuente:** RFP-AgroInteligente-Colombia.md — Secciones 5.10, 9; RFP-inicial.md — Sección 3 (Recomendaciones Inteligentes)
**Prioridad:** Alta (Crítica — núcleo del negocio)

## Descripción
Este es el requerimiento central del negocio. Dado un conjunto de mediciones de sensores para un terreno y un cultivo objetivo (o el motor sugiriendo el cultivo más apto), el sistema debe:

1. **Determinar la aptitud del suelo:** evaluar si el suelo cumple las condiciones ideales para obtener una excelente cosecha del cultivo evaluado, comparando cada variable contra los umbrales de la ficha técnica del cultivo.

2. **Identificar desviaciones:** si el suelo no cumple las condiciones ideales, identificar cada variable fuera de rango (pH, nutrientes, humedad), su severidad y nivel de prioridad.

3. **Generar recomendaciones correctivas:** por cada desviación, generar una recomendación específica y accionable (ej. "El terreno requiere incrementar el nivel de Potasio en X kg/ha", "No se recomienda sembrar café debido al nivel de acidez — pH actual: 4.8, pH ideal: 5.5–6.5").

4. **Justificar cada recomendación:** toda recomendación debe estar acompañada de:
   - Variables que influyeron en la decisión.
   - Nivel de confianza de la predicción.
   - Riesgos de no aplicar la corrección.
   - Beneficios esperados de aplicar la corrección.
   - Costo estimado de la intervención.
   - Impacto esperado en el rendimiento.

5. **No alucinar:** el sistema nunca debe inventar información. Si no hay evidencia suficiente para una recomendación, debe indicarlo explícitamente: "No hay datos suficientes para determinar...".

## Actores involucrados
- Cliente (Agricultor) — recibe las recomendaciones
- Técnico Agrónomo — revisa y valida las recomendaciones

## Criterios de aceptación
- Cada recomendación incluye justificación completa con nivel de confianza.
- Las recomendaciones se expresan en lenguaje natural, entendible para un agricultor sin conocimientos técnicos.
- El sistema indica explícitamente cuando no tiene suficiente información para recomendar.
- No especificados en el RFP — definir: ¿umbral mínimo de confianza para mostrar una recomendación?, ¿formato de salida (texto libre, estructurado, ambos)?

## Dependencias / relacionados
- RF-009: Catálogo de cultivos (umbrales de referencia)
- RF-010: Motor de conocimiento agronómico
- RF-012: Motor predictivo (modelos 1–4)
- RF-014: Agente IA
- RNF-010: No alucinación del sistema

## Notas del analista
- Este requisito es el diferenciador principal de la plataforma. La calidad de las recomendaciones determinará la adopción y retención de usuarios.
- La combinación de sistema experto (reglas) + ML es clave: las reglas aseguran que las recomendaciones tengan sentido agronómico, y los modelos de ML permiten capturar interacciones complejas entre variables que las reglas simples no pueden modelar.
- La metodología de la UPRA para clasificación de aptitud de tierras (Alta/Media/Baja/No apta) debe ser la base del sistema de clasificación, lo que da respaldo institucional y validación científica.
