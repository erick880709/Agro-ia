---
id: TT-05
type: Tarea Técnica
epic: 011
priority: Alta
points: 3
---

# TT-05: Persistencia de preferencias de lectura en el perfil

## Descripción
Guardar en el perfil del usuario la activación, la voz elegida y la velocidad para sincronizarlas entre sesiones y dispositivos.

## Criterios de Done
- [ ] Preferencias (activado, voz, velocidad) persistidas por cuenta.

## Recurso de datos involucrado

### Recurso
- **Nombre:** PreferenciaLecturaVoz
- **Capa(s):** backend

### Campos del recurso
| Campo | Tipo | Requerido | Descripción / Restricciones |
|---|---|---|---|
| usuario_id | UUID | Sí | Dueño de la preferencia |
| activado | booleano | Sí | Lectura activa/inactiva |
| voz | texto | Sí | femenina / masculina / mi-voz |
| velocidad | texto | No | 0.75 / 1 / 1.25 / 1.5 |

### Relaciones con otros recursos
- `Usuario` (1:1).

## Dependencias
- Ninguna
