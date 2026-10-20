# RF-045: Detención automática de la lectura

**Tipo:** Requerimiento funcional
**Fuente:** RFP-AGROIA-002 — Secciones 6.1 y 7 (RF-08)
**Prioridad:** Mandatoria (M)

## Descripción
La lectura en curso debe detenerse de inmediato al apagar la función, al enviar una nueva consulta o al salir del chat.

## Actores involucrados
- Productor / agricultor
- Técnico / extensionista

## Criterios de aceptación
- Al apagar la función, la lectura en curso se detiene de inmediato.
- Al enviar una nueva consulta o salir del chat, la lectura se detiene.

## Dependencias / relacionados
- RF-038: Interruptor de lectura
- RF-043: Controles de reproducción

## Notas del analista
Conviene coordinar con RF-041 para evitar que la detención y la lectura automática de una nueva respuesta compitan en el mismo instante.
