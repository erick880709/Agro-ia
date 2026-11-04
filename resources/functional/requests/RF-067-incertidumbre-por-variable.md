# RF-067: Incertidumbre por variable

**Tipo:** Requerimiento funcional
**Fuente:** RFP-AGROIA-003 §6 (Requerimientos, Épica E3)
**Prioridad:** No especificada

## Descripción
Tabla parametrizable de incertidumbre por variable (valores iniciales en el Anexo A). Se calcula la incertidumbre estándar con criterio de distribución rectangular (exactitud/√3) y se guarda con la lectura. Para humedad se usa la exactitud por tramo (±3 % ≤53 %, ±5 % >53 %).

## Actores involucrados
Motor de calidad, orquestador

## Criterios de aceptación
No especificados en el RFP — definir con el cliente.

## Dependencias / relacionados
RT-032 (Anexo A); RD-011 (`incertidumbre` en sensor_readings).

## Notas del analista
H-07: hoy se muestra falsa precisión (0,01 de pH, 1 mg/kg) ignorando ±0,3 y ±40.
