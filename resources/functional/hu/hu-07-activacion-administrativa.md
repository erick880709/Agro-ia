---
id: HU-07
type: Historia de Usuario
epic: 010
priority: Baja
points: 3
---

# HU-07: Activación administrativa de la función de voz

## Como
Administrador

## Quiero
Activar o desactivar la función de voz desde Administración → Parámetros

## Para
Controlar la disponibilidad de la función sin desplegar código

## Criterios de Aceptación
- [ ] CA1: El administrador puede activar y desactivar la función desde el área indicada.
- [ ] CA2: Al desactivarla, el botón de micrófono se oculta o deshabilita en todos los clientes.

## Recurso de datos involucrado

### Recurso
- **Nombre:** ParametroVoz (campo `activado`; definición completa en TT-03)
- **Capa(s):** backend / frontend

### Campos del recurso
| Campo | Tipo | Requerido | Descripción / Restricciones |
|---|---|---|---|
| activado | booleano | Sí | Activa/desactiva la función de voz |

### Relaciones con otros recursos
- Ninguna.
