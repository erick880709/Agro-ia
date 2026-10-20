# RF-050: Preferencia de voz sincronizada entre dispositivos

**Tipo:** Requerimiento funcional
**Fuente:** RFP-AGROIA-002 — Secciones 7 (RF-13) y 10
**Prioridad:** Deseable (D)

## Descripción
La preferencia de activación, la voz elegida y la velocidad deben respetarse en todos los dispositivos del usuario.

## Actores involucrados
- Productor / agricultor
- Técnico / extensionista

## Criterios de aceptación
- La preferencia de activación, voz y velocidad se conserva y respeta en los dispositivos del usuario.

## Dependencias / relacionados
- RF-038: Interruptor persistente
- RF-044: Control de velocidad
- RT-025: Persistencia de preferencias en el perfil

## Notas del analista
Implica guardar las preferencias en el perfil del usuario en el backend (no solo en `localStorage`). El RFP lo marca deseable; en Fase 1 podría limitarse al dispositivo actual.
