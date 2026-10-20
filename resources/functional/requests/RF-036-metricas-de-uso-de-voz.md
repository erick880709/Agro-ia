# RF-036: Métricas de uso de voz sin almacenar audio

**Tipo:** Requerimiento funcional
**Fuente:** RFP-AGROIA-001 — Secciones 7 (RF-14), 9.2 y 10
**Prioridad:** Deseable (D)

## Descripción
La plataforma debe registrar métricas de uso de la función de voz: cantidad de consultas, errores y duración. No debe almacenar audio ni ampliar el registro del contenido de las consultas más allá de lo que ya registra el chat.

## Actores involucrados
- Administrador
- Productor / agricultor
- Técnico / extensionista

## Criterios de aceptación
- Se pueden contabilizar consultas por voz, errores y duración.
- El registro no almacena audio ni contenido adicional de las consultas.

## Dependencias / relacionados
- RNF-019: Retención y tratamiento de audio
- RNF-022: Minimización de registros de consultas

## Notas del analista
El RFP no especifica retención, granularidad, panel de consulta ni si las métricas deben asociarse a usuarios identificables.
