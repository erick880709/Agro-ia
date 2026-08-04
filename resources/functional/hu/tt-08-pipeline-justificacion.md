---
id: TT-08
type: Tarea Técnica
epic: 001-motor-recomendaciones
priority: Media
points: 5
---

# TT-08: Implementar pipeline de justificación de recomendaciones

## Descripción
Construir el módulo que genera la explicación en lenguaje natural de cada recomendación: variables que influyeron, nivel de confianza, riesgos, beneficios, costo estimado e impacto esperado. Debe funcionar en dos modos: lenguaje coloquial (agricultor) y lenguaje técnico (técnico/investigador).

## Criterios de Done
- [ ] Plantillas de justificación por tipo de recomendación (fertilización, corrección pH, cultivo ideal)
- [ ] Traducción de valores técnicos a lenguaje coloquial (ej. "pH 4.8" → "su suelo es muy ácido")
- [ ] Inclusión de fuente de la recomendación (ML, regla agronómica, técnico)
- [ ] Cálculo de costo estimado en COP con base en área (ha) y precio de referencia del insumo
- [ ] Estimación de impacto esperado (ej. "+0.3 a +0.6 ton/ha si corrige el pH")
- [ ] Modo dual: el mismo pipeline genera versión coloquial y versión técnica

## Dependencias
TT-03, TT-04
