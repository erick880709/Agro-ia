---
id: TT-04
type: Tarea Técnica
epic: RFP-AGROIA-003
priority: Alta
points: 8
---

# TT-04: Motor de calidad con 10 estados

## Descripción
Ampliar el enum calidad a 10 estados (valida, valida_con_advertencia, bajo_limite_deteccion, saturada, fuera_de_rango, sonda_fuera_de_suelo, humedad_insuficiente, no_calibrada, estimado_sig, invalidada) y guardar motivos_calidad[] y version_regla por lectura.

## Criterios de Done
- [ ] Migración del enum aplicada y reversible.
- [ ] Cada lectura guarda motivos_calidad[] y version_regla.

## Dependencias
- TT-01

## Recurso de datos involucrado

### Recurso
- **Nombre:** SensorReading
- **Capa(s):** backend

### Campos del recurso
| Campo | Tipo | Requerido | Descripción / Restricciones |
|---|---|---|---|
| calidad | enum ampliado | Sí | 10 estados de calidad. |
| motivos_calidad | text[] | Sí | Lista de motivos de la clasificación. |
| version_regla | string | Sí | Versión de la regla aplicada. |
| valor_crudo | int | Sí | Valor entero crudo del registro Modbus. |
| valor_escalado | decimal | Sí | Valor escalado con su unidad. |
| valor_normalizado | decimal | No | Valor en unidad de análisis. |
| unidad | string | Sí | Unidad del valor escalado. |
| incertidumbre | decimal | No | Incertidumbre estándar calculada. |
| grado_evidencia | enum | No | A | B | C | D. |
| profundidad_cm | int | No | Profundidad de la lectura. |
| punto_id | string | No | Punto de muestreo. |
| replica_n | int | No | Número de réplica. |
| sesion_muestreo_id | FK | No | Sesión de muestreo. |
| vwc_pct | decimal | No | Humedad volumétrica (%). |
| ce_25c_dsm | decimal | No | CE normalizada a 25 °C (dS/m). |

## Subtareas
- [ ] Migración del enum calidad.
- [ ] Asignación de estados desde el motor.
- [ ] Persistencia de motivos y versión de regla.
