---
id: HU-13
type: Historia de Usuario
epic: RFP-AGROIA-003
priority: Alta
points: 8
---

# HU-13: Administrar parámetros de calidad

## Como
administrador

## Quiero
gestionar rangos, saturación, humedad mínima, tolerancias, ventanas e incertidumbres con auditoría y versionado

## Para
ajustarlos sin tocar código.

## Criterios de Aceptación
- [ ] CA1: Todo parámetro es editable desde administración.
- [ ] CA2: Cada cambio queda auditado (quién, cuándo, antes/después).
- [ ] CA3: Cada lectura guarda la versión de regla aplicada.

## Recurso de datos involucrado

### Recurso
- **Nombre:** ParametroCalidadSensor
- **Capa(s):** backend

### Campos del recurso
| Campo | Tipo | Requerido | Descripción / Restricciones |
|---|---|---|---|
| parametro | string | Sí | Nombre del parámetro (rango, saturación, humedad mínima, etc.). |
| valor | string | Sí | Valor del parámetro (JSON o escalar). |
| version | int | Sí | Versión de la regla. |
| audit_actor | string | Sí | Quién hizo el cambio. |
| audit_fecha | datetime | Sí | Cuándo se hizo. |

### Relaciones con otros recursos
- Sin relaciones definidas en la épica.

## Subtareas
- [ ] Dividir formulario de parámetros por categoría (rangos, saturación, contexto, incertidumbre).
- [ ] Implementar historial de versiones con diff antes/después.
