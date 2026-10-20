# RT-025: Persistencia de preferencias de voz en el perfil

**Tipo:** Requisito técnico
**Categoría:** Configuración
**Fuente:** RFP-AGROIA-002 — Secciones 7 (RF-13) y 10

## Descripción
La preferencia de activación, la voz elegida y la velocidad deben guardarse en el perfil del usuario para respetarse entre sesiones y dispositivos.

## Criterio medible / restricción concreta
Persistencia en el perfil de: activación, voz elegida y velocidad. El RFP no define el modelo de datos exacto.

## Impacto en la arquitectura
Extender el perfil de usuario con las preferencias de lectura; alimenta la sincronización multi-dispositivo (RF-050).

## Notas del analista
Debe definirse el alcance de Fase 1: el RFP marca la sincronización entre dispositivos como deseable (RF-13), pudiendo limitarse a `localStorage` en una primera entrega.
