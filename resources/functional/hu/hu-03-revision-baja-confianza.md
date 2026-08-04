---
id: HU-03
type: Historia de Usuario
epic: 001-motor-recomendaciones
priority: Alta
points: 5
---

# HU-03: Revisar recomendaciones de baja confianza

## Como
Técnico Agrónomo

## Quiero
Revisar las recomendaciones con F1-score < 0.80 que me fueron escaladas

## Para
Validarlas, corregirlas o aprobarlas en un plazo máximo de 10 días hábiles

## Criterios de Aceptación
- [ ] CA1: El técnico ve una cola de casos pendientes de revisión (DISC-XXXX) ordenados por antigüedad
- [ ] CA2: Puede anotar, corregir la predicción del modelo, o aprobar la recomendación original
- [ ] CA3: Cada caso muestra un contador de días restantes del SLA (≤ 10 días hábiles)
- [ ] CA4: Si pasan > 10 días sin revisión, la recomendación se bloquea automáticamente y se notifica al administrador
- [ ] CA5: Las correcciones del técnico quedan registradas como feedback para reentrenamiento futuro

## Recurso de datos involucrado
### Recurso
- **Nombre:** Discordancia
- **Capa(s):** backend

### Campos del recurso
| Campo | Tipo | Requerido | Descripción / Restricciones |
|---|---|---|---|
| id | UUID | Sí | Identificador único (DISC-XXXX) |
| recomendacion_id | UUID | Sí | FK a Recomendacion |
| prediccion_ml | JSONB | Sí | Salida del modelo ML |
| regla_aplicada | JSONB | Sí | Regla del sistema experto que bloqueó |
| motivo_conflicto | Text | Sí | Descripción del conflicto ML vs reglas |
| estado | Enum(Pendiente/Revisada/Bloqueada) | Sí | Estado del caso |
| resolucion | Text | No | Decisión del técnico |
| tecnico_id | UUID | No | FK a Usuario (técnico revisor) |
| sla_vencimiento | Timestamp | Sí | Fecha límite (created_at + 10 días hábiles) |
| created_at | Timestamp | Sí | Fecha de creación |

## Subtareas
- [ ] Implementar cola de casos pendientes con ordenamiento y filtros
- [ ] Construir formulario de revisión con anotaciones y corrección
- [ ] Implementar job programado de bloqueo automático tras 10 días
