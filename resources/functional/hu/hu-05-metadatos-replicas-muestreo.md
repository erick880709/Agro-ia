---
id: HU-05
type: Historia de Usuario
epic: RFP-AGROIA-003
priority: Alta
points: 3
---

# HU-05: Registrar metadatos y réplicas de muestreo

## Como
técnico de campo

## Quiero
registrar profundidad, réplica, pedregosidad, estabilización, observaciones y foto

## Para
que cada lectura sea reproducible y trazable.

## Criterios de Aceptación
- [ ] CA1: La sesión guarda punto, réplicas y profundidad (cm).
- [ ] CA2: Se puede adjuntar foto opcional y observaciones.
- [ ] CA3: El número de réplica queda asociado a cada lectura.

## Recurso de datos involucrado

### Recurso
- **Nombre:** SesionMuestreo
- **Capa(s):** backend

### Campos del recurso
| Campo | Tipo | Requerido | Descripción / Restricciones |
|---|---|---|---|
| punto_id | string | Sí | Identificador del punto de muestreo. |
| replicas | int | Sí | Número de réplicas del punto. |
| profundidad_cm | int | Sí | Profundidad (centro de la capa). |
| pedregosidad | string | No | Pedregosidad del punto. |
| tiempo_estabilizacion | int | No | Tiempo de estabilización (s). |
| observaciones | text | No | Observaciones libres. |
| foto_url | string | No | Foto opcional. |

### Relaciones con otros recursos
- `SensorReading` (1:N): Una sesión agrupa varias lecturas con réplica.

