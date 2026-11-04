---
id: HU-01
type: Historia de Usuario
epic: RFP-AGROIA-003
priority: Alta
points: 5
---

# HU-01: Registrar sensores con su configuración

## Como
administrador

## Quiero
registrar cada dispositivo (modelo, variante, dirección Modbus, baudios, instalación, profundidad, modo, lote)

## Para
garantizar unicidad dirección↔bus y trazabilidad del parque de sensores.

## Criterios de Aceptación
- [ ] CA1: El alta exige modelo, variante, dirección Modbus y baudios.
- [ ] CA2: Se rechaza un segundo sensor con la misma dirección en el mismo bus.
- [ ] CA3: Cada sensor queda vinculado a lote, profundidad y modo (superficial/enterrado).

## Recurso de datos involucrado

### Recurso
- **Nombre:** DispositivoIoT
- **Capa(s):** backend

### Campos del recurso
| Campo | Tipo | Requerido | Descripción / Restricciones |
|---|---|---|---|
| modelo | string | Sí | Modelo del sensor (JXBS-3001-NPK-RS / variante TR). |
| variante | string | Sí | Variante (a confirmar con etiqueta física, fase 0). |
| direccion_modbus | int | Sí | Dirección Modbus, única por bus. |
| baudios | int | Sí | Baudios (9600 8N1 por defecto). |
| firmware | string | No | Versión de firmware del dispositivo. |
| fecha_instalacion | date | No | Fecha de instalación en campo. |
| profundidad_cm | int | No | Profundidad de instalación o lectura. |
| modo_instalacion | enum | Sí | superficial | enterrado. |
| lote_id | FK | Sí | Lote al que pertenece. |
| ultimo_mantenimiento | date | No | Fecha del último mantenimiento. |
| estado_salud | string | No | Estado de salud agregado. |

### Relaciones con otros recursos
- `Lote` (N:1): Un lote puede tener varios dispositivos; un dispositivo pertenece a un lote.

