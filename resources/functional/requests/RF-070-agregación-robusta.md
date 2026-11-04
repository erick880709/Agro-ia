# RF-070: Agregación robusta

**Tipo:** Requerimiento funcional
**Fuente:** RFP-AGROIA-003 §6 (Requerimientos, Épica E3)
**Prioridad:** No especificada

## Descripción
Valor por punto = mediana de réplicas; valor por lote = estadístico con intervalo. El mapa de calor solo se genera con un mínimo parametrizable de puntos válidos y muestra la incertidumbre de interpolación.

## Actores involucrados
Motor de calidad, sistema de reportes

## Criterios de aceptación
No especificados en el RFP — definir con el cliente.

## Dependencias / relacionados
RF-070; RF-065 (MAD).

## Notas del analista
H-08: sin réplicas ni puntos mínimos, los mapas y promedios por lote no son representativos.
