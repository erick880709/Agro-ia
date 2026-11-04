# RF-091: Entrenar modelos con etiquetas de laboratorio

**Tipo:** Requerimiento funcional
**Fuente:** RFP-AGROIA-003 §6 (Requerimientos, Épica E9)
**Prioridad:** No especificada

## Descripción
Entrenar y evaluar los modelos con etiquetas de laboratorio, nunca con salidas de reglas aplicadas al mismo sensor. Incluir las covariables de contexto (humedad, temperatura, CE) y la incertidumbre.

## Actores involucrados
Servicio ML, científico de datos

## Criterios de aceptación
No especificados en el RFP — definir con el cliente.

## Dependencias / relacionados
RF-073 (pares sensor-lab); RF-092.

## Notas del analista
H-09: circularidad si las etiquetas derivan de reglas sobre el propio sensor.
