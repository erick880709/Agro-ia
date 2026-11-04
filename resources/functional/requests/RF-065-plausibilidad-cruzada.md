# RF-065: Plausibilidad cruzada

**Tipo:** Requerimiento funcional
**Fuente:** RFP-AGROIA-003 §6 (Requerimientos, Épica E2)
**Prioridad:** No especificada

## Descripción
Reglas parametrizables de plausibilidad: saltos de temperatura incompatibles con la inercia del suelo, temperatura >45 °C (sol directo), NPK alto con CE ≈ 0, y variación entre réplicas del mismo punto fuera de tolerancia (detección con mediana y MAD).

## Actores involucrados
Motor de calidad

## Criterios de aceptación
No especificados en el RFP — definir con el cliente.

## Dependencias / relacionados
RF-062; RF-070 (agregación).

## Notas del analista
La detección con mediana/MAD es robusta a valores atípicos.
