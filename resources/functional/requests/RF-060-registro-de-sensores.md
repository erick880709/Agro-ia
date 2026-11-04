# RF-060: Registro de sensores

**Tipo:** Requerimiento funcional
**Fuente:** RFP-AGROIA-003 §6 (Requerimientos, Épica E1)
**Prioridad:** No especificada

## Descripción
Por cada dispositivo se registra: modelo y variante, dirección Modbus, baudios, fecha de instalación, profundidad, modo de instalación (superficial o enterrado), lote asociado y último mantenimiento. Se garantiza unicidad de dirección ↔ bus.

## Actores involucrados
Administrador, técnico de campo

## Criterios de aceptación
No especificados en el RFP — definir con el cliente.

## Dependencias / relacionados
RD-011 (modelo de datos `dispositivos_iot`); RF-089 (mantenimiento).

## Notas del analista
H-15: sin mapeo dirección↔sensor↔lote↔profundidad las lecturas pueden atribuirse mal.
