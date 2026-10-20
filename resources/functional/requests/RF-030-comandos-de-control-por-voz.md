# RF-030: Comandos de control por voz

**Tipo:** Requerimiento funcional
**Fuente:** RFP-AGROIA-001 — Secciones 4.1, 7 (RF-08), 7.1 y 18
**Prioridad:** Deseable (D)

## Descripción
El chat debe admitir los comandos de control “enviar”, “borrar”, “cancelar” y “repetir”. “Enviar” manda el texto actual; “borrar” y “cancelar” limpian el campo; “repetir” descarta la transcripción y reinicia la captura. Los comandos solo se reconocen cuando se pronuncian solos, para no confundirlos con el contenido de una consulta.

## Actores involucrados
- Productor / agricultor
- Técnico / extensionista

## Criterios de aceptación
- Cuando se implementa, los cuatro comandos producen las acciones descritas y se reconocen únicamente si se pronuncian solos.
- La inclusión de esta función en Fase 1 debe confirmarse con el solicitante.

## Dependencias / relacionados
- RF-027: Revisión y edición de la transcripción
- RF-028: Envío al servicio de chat existente

## Notas del analista
La inclusión en Fase 1 aparece como decisión abierta en la sección 18, aunque RF-08 está marcado como deseable.
