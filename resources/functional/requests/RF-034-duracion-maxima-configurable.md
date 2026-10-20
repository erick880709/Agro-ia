# RF-034: Duración máxima configurable de grabación

**Tipo:** Requerimiento funcional
**Fuente:** RFP-AGROIA-001 — Secciones 7 (RF-12), 9.2 y 10
**Prioridad:** Mandatoria (M)

## Descripción
El sistema debe limitar la duración máxima de una grabación por consulta. El límite debe poder parametrizarse y no quedar fijo en el código.

## Actores involucrados
- Productor / agricultor
- Técnico / extensionista
- Administrador

## Criterios de aceptación
- Existe un límite máximo por consulta y este puede configurarse.
- El valor concreto y el comportamiento al alcanzarlo se definen antes de la puesta en producción.

## Dependencias / relacionados
- RT-019: Parámetros administrables
- RNF-023: Límites contra abuso

## Notas del analista
El RFP no establece el valor del límite ni si al alcanzarlo se detiene automáticamente la captura o se presenta una confirmación.
