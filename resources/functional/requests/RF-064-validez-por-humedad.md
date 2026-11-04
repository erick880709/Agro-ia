# RF-064: Validez por humedad

**Tipo:** Requerimiento funcional
**Fuente:** RFP-AGROIA-003 §6 (Requerimientos, Épica E2)
**Prioridad:** No especificada

## Descripción
Si la VWC está por debajo de un mínimo parametrizable (valor inicial 15 %, a confirmar en campo), pH, CE y NPK pasan a `humedad_insuficiente`. Humedad y CE cercanas a 0 simultáneamente indican `sonda_fuera_de_suelo`.

## Actores involucrados
Motor de calidad

## Criterios de aceptación
No especificados en el RFP — definir con el cliente.

## Dependencias / relacionados
RF-062; RT-032.

## Notas del analista
H-04: sin validación de contexto, pH/CE/NPK espurios pasan el filtro de rango.
