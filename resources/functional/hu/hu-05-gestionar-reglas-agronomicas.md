---
id: HU-05
type: Historia de Usuario
epic: 001-motor-recomendaciones
priority: Media
points: 5
---

# HU-05: Gestionar reglas agronómicas del sistema experto

## Como
Técnico Agrónomo

## Quiero
Crear, editar y versionar las reglas del sistema experto agronómico

## Para
Mantener actualizado el conocimiento agronómico oficial (UPRA, Cenicafé, AGROSAVIA)

## Criterios de Aceptación
- [ ] CA1: CRUD completo de reglas con registro de auditoría (quién, cuándo, qué cambió)
- [ ] CA2: Cada regla tiene: cultivo(s) aplicable, variable de suelo, umbral (mín/máx), acción recomendada, prioridad
- [ ] CA3: Las reglas se versionan; se puede ver el historial de cambios y revertir a una versión anterior
- [ ] CA4: Se puede simular una regla contra datos históricos para ver cuántas recomendaciones habría afectado antes de publicarla

## Recurso de datos involucrado
### Recurso
- **Nombre:** ReglaAgronomica
- **Capa(s):** backend / frontend

### Campos del recurso
| Campo | Tipo | Requerido | Descripción / Restricciones |
|---|---|---|---|
| id | UUID | Sí | Identificador único |
| cultivo_id | UUID | Sí | FK a Cultivo (o null para regla universal) |
| variable | Enum(pH/N/P/K/...) | Sí | Variable de suelo |
| umbral_min | Float | No | Valor mínimo aceptable |
| umbral_max | Float | No | Valor máximo aceptable |
| accion | Text | Sí | Recomendación correctiva |
| prioridad | Enum(Critica/Alta/Media/Baja) | Sí | Nivel de prioridad |
| fuente | String | Sí | Origen (UPRA, Cenicafé, AGROSAVIA, Manual) |
| version | Integer | Sí | Número de versión |
| activa | Boolean | Sí | Si está activa en producción |
| created_at | Timestamp | Sí | Fecha de creación |

## Subtareas
- [ ] Construir CRUD de reglas con formulario de edición
- [ ] Implementar versionado de reglas (tabla historial)
- [ ] Construir simulador de reglas contra datos históricos
