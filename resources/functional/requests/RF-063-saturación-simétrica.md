# RF-063: Saturación simétrica

**Tipo:** Requerimiento funcional
**Fuente:** RFP-AGROIA-003 §6 (Requerimientos, Épica E2)
**Prioridad:** No especificada

## Descripción
pH ≤ límite inferior o ≥ límite superior, CE ≥ 10 dS/m y N, P o K ≥ 1999 mg/kg se marcan `saturada`. Un 0 en CE o NPK se marca `bajo_limite_deteccion` y se conserva para análisis con su incertidumbre, sin tratarlo como error.

## Actores involucrados
Motor de calidad

## Criterios de aceptación
No especificados en el RFP — definir con el cliente.

## Dependencias / relacionados
RF-062; RT-032 (Anexo A).

## Notas del analista
H-10: los límites actuales son asimétricos y descartan información de suelos realmente pobres.
