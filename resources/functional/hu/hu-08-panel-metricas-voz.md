---
id: HU-08
type: Historia de Usuario
epic: 010
priority: Baja
points: 3
---

# HU-08: Panel de métricas de uso de voz

## Como
Administrador

## Quiero
Consultar métricas agregadas de uso de la función (consultas por voz, errores y duración media) sin ver audio ni contenido

## Para
Monitorear la adopción y el desempeño de la función

## Criterios de Aceptación
- [ ] CA1: Se pueden contabilizar consultas por voz, errores y duración media, agregadas mensualmente.
- [ ] CA2: El administrador dispone de un panel simple para consultar estas métricas.
- [ ] CA3: Las métricas no almacenan audio ni contenido de consultas ni se asocian a usuarios individuales.

## Recurso de datos involucrado

### Recurso
- **Nombre:** MetricaUsoVoz
- **Capa(s):** backend / frontend

### Campos del recurso
| Campo | Tipo | Requerido | Descripción / Restricciones |
|---|---|---|---|
| periodo | fecha (mes) | Sí | Periodo de agregación mensual |
| consultas_por_voz | entero | Sí | Cantidad de consultas enviadas por voz |
| errores | entero | Sí | Cantidad de errores de captura/transcripción |
| duracion_media | numérico | Sí | Duración media de las consultas; unidad no especificada en la épica — definir con negocio |

### Relaciones con otros recursos
- Ninguna (agregado anónimo; no asociado a usuarios). No especificado en la épica — definir con negocio si se requiere retención o granularidad distinta.
