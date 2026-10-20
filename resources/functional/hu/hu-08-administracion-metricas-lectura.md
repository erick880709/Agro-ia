---
id: HU-08
type: Historia de Usuario
epic: 011
priority: Media
points: 3
---

# HU-08: Administración y métricas de la lectura

## Como
Administrador

## Quiero
Activar/desactivar la función y la voz personalizada, fijar límites y ver métricas de uso sin audio

## Para
Gobernar la función y controlar costos

## Criterios de Aceptación
- [ ] CA1: El administrador activa/desactiva la lectura y la voz personalizada y fija límites desde Administración → Parámetros.
- [ ] CA2: Se registran activaciones, voz elegida, errores y caracteres leídos, sin audio.

## Recurso de datos involucrado

### Recurso
- **Nombre:** MetricaLecturaVoz
- **Capa(s):** backend

### Campos del recurso
| Campo | Tipo | Requerido | Descripción / Restricciones |
|---|---|---|---|
| periodo | texto | Sí | Periodo de agregación (YYYY-MM) |
| activaciones | entero | Sí | Veces que se activó la lectura |
| voz_elegida | texto | Sí | Voz seleccionada |
| errores | entero | Sí | Errores de síntesis/reproducción |
| caracteres_leidos | entero | Sí | Consumo para control de cuota |

### Relaciones con otros recursos
- Ninguna (agregado anónimo).
