---
id: TT-05
type: Tarea Técnica
epic: RFP-AGROIA-003
priority: Alta
points: 8
---

# TT-05: Reglas de validez parametrizables

## Descripción
Saturación simétrica (pH/CE/NPK), bajo_limite_deteccion para 0 en CE/NPK, validez por humedad mínima (15 % inicial), sonda_fuera_de_suelo (humedad≈0 y CE≈0) y plausibilidad cruzada con mediana/MAD.

## Criterios de Done
- [ ] Unit tests con vectores de saturación y sonda fuera de suelo.
- [ ] Las reglas son parametrizables, sin valores fijos en código.

## Dependencias
- TT-04

