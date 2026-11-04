---
id: HU-04
type: Historia de Usuario
epic: RFP-AGROIA-003
priority: Alta
points: 5
---

# HU-04: Registrar pares sensor–laboratorio

## Como
agrónomo

## Quiero
registrar pares sensor–laboratorio (mismo punto, misma profundidad y día, método, laboratorio, fecha)

## Para
alimentar la calibración local por unidad de suelo.

## Criterios de Aceptación
- [ ] CA1: El par exige muestra compuesta del mismo punto y profundidad del mismo día.
- [ ] CA2: Se registra método de laboratorio, laboratorio y fecha.
- [ ] CA3: El sistema alerta cuando una calibración está vencida.

## Recurso de datos involucrado

### Recurso
- **Nombre:** ParCalibracion
- **Capa(s):** backend

### Campos del recurso
| Campo | Tipo | Requerido | Descripción / Restricciones |
|---|---|---|---|
| lectura_sensor_id | FK | Sí | Lectura del sensor del punto. |
| resultado_laboratorio | decimal | Sí | Resultado del laboratorio (método declarado). |
| metodo | string | Sí | Método de laboratorio (pH 1:1, Bray II, etc.). |
| laboratorio | string | Sí | Laboratorio acreditado (ej. AGROSAVIA Tibaitatá 13-LAB-031). |
| fecha | date | Sí | Fecha del par. |

### Relaciones con otros recursos
- `CalibracionSensor` (N:1): Varios pares alimentan una calibración.

