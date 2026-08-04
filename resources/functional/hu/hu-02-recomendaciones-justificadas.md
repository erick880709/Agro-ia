---
id: HU-02
type: Historia de Usuario
epic: 001-motor-recomendaciones
priority: Alta
points: 5
---

# HU-02: Recibir recomendaciones correctivas justificadas

## Como
Agricultor

## Quiero
Ver recomendaciones correctivas con justificación completa, costo estimado e impacto esperado

## Para
Decidir informadamente si aplico o no las recomendaciones en mi cultivo

## Criterios de Aceptación
- [ ] CA1: Cada recomendación muestra: variables que influyeron, nivel de confianza, riesgos, beneficios, costo estimado (COP/ha) e impacto esperado
- [ ] CA2: El texto de la recomendación está en lenguaje natural coloquial entendible por un agricultor no técnico
- [ ] CA3: Se puede ver el historial completo de recomendaciones por finca, ordenado cronológicamente
- [ ] CA4: El costo estimado se calcula con base en el área de la finca (ha) y el precio de referencia del insumo

## Subtareas
- [ ] Implementar pipeline de justificación (plantillas por tipo de recomendación)
- [ ] Construir UI de detalle de recomendación con desglose de variables
- [ ] Integrar cálculo de costo estimado en COP
