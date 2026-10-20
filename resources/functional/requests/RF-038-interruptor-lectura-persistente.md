# RF-038: Interruptor de lectura de respuestas con estado persistente

**Tipo:** Requerimiento funcional
**Fuente:** RFP-AGROIA-002 — Secciones 3, 4.1, 6.1 y 7 (RF-01)
**Prioridad:** Mandatoria (M)

## Descripción
El chat y las preferencias del usuario deben ofrecer un interruptor visible para activar o desactivar la lectura en voz alta de las respuestas del Asesor agronómico. La preferencia debe persistir entre sesiones del mismo usuario.

## Actores involucrados
- Productor / agricultor
- Técnico / extensionista

## Criterios de aceptación
- El usuario puede activar y desactivar la lectura de respuestas desde el chat y desde sus preferencias.
- La preferencia se conserva entre sesiones.

## Dependencias / relacionados
- RF-045: Detención automática al apagar
- RF-050: Sincronización de la preferencia entre dispositivos
- RNF-024: Usabilidad de la lectura

## Notas del analista
El RFP menciona persistencia "por usuario" (RF-01) y sincronización "en todos los dispositivos" (RF-13, deseable). Debe definirse si la preferencia es una sola a nivel de cuenta (multi-dispositivo) o por dispositivo en Fase 1.
