---
id: TT-08
type: Tarea Técnica
epic: RFP-AGROIA-003
priority: Alta
points: 8
---

# TT-08: Modelo de calibración por regresión lineal

## Descripción
Sustituir el factor único por regresión lineal (pendiente/intercepto) por dispositivo, variable y unidad de suelo, con n, R², RMSE, sesgo, vigencia y responsable; historial; curvas de humedad (VWC vs gravimétrico × densidad aparente) y CE (patrón, normalización a 25 °C, CE 1:5 y CEe).

## Criterios de Done
- [ ] Regresión lineal con métricas y vigencia persistidas.
- [ ] Historial de calibraciones por dispositivo y variable.

## Dependencias
- TT-04

## Recurso de datos involucrado

### Recurso
- **Nombre:** CalibracionSensor
- **Capa(s):** backend

### Campos del recurso
| Campo | Tipo | Requerido | Descripción / Restricciones |
|---|---|---|---|
| dispositivo_id | FK | Sí | Dispositivo calibrado. |
| variable | string | Sí | Variable calibrada (pH, humedad, CE, N, P, K). |
| unidad_suelo | string | Sí | Unidad de suelo de la calibración. |
| pendiente | decimal | Sí | Pendiente de la regresión. |
| intercepto | decimal | Sí | Intercepto de la regresión. |
| n | int | Sí | Número de pares. |
| r2 | decimal | Sí | Coeficiente de determinación. |
| rmse | decimal | Sí | Raíz del error cuadrático medio. |
| sesgo | decimal | Sí | Sesgo frente a laboratorio. |
| vigencia | date | Sí | Fecha de vencimiento. |

## Subtareas
- [ ] Migración de calibracion_sensor.
- [ ] Cálculo de regresión y métricas.
- [ ] Histórico y vencimiento.
