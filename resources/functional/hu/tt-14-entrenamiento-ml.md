---
id: TT-14
type: Tarea Técnica
epic: RFP-AGROIA-003
priority: Media
points: 8
---

# TT-14: Entrenamiento ML con etiquetas de laboratorio

## Descripción
Entrenar y evaluar los modelos solo con etiquetas de laboratorio (nunca con salidas de reglas sobre el mismo sensor); incluir covariables de contexto (humedad, temperatura, CE) e incertidumbre.

## Criterios de Done
- [ ] Pipeline de entrenamiento usa pares sensor–laboratorio.
- [ ] Covariables de contexto e incertidumbre incluidas.

## Dependencias
- TT-08

## Subtareas
- [ ] Dataset de pares sensor–laboratorio.
- [ ] Features con contexto e incertidumbre.
- [ ] Evaluación por unidad de suelo.
