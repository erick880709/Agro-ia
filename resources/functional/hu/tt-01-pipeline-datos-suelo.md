---
id: TT-01
type: Tarea Técnica
epic: 001-motor-recomendaciones
priority: Alta
points: 5
---

# TT-01: Implementar pipeline de datos de suelo (18 variables)

## Descripción
Crear los Data Adapters que normalizan y validan las 18 variables de suelo desde PostgreSQL+TimescaleDB, incluyendo la clasificación de variables bloqueantes vs no bloqueantes.

## Criterios de Done
- [ ] SueloAdapter: consulta y normaliza variables desde `sensor_data` (pH, N, P, K, Ca, Mg, S, Fe, Mn, Zn, Cu, B, MO, CIC, textura, humedad, temperatura, CE)
- [ ] ClimaAdapter: obtiene datos climáticos desde cache IDEAM
- [ ] NDVIAdapter: obtiene último NDVI desde Copernicus
- [ ] GISAdapter: consulta ubicación y altitud desde PostGIS
- [ ] Validación de rangos físicos (pH 0-14, etc.)
- [ ] Detección de variables faltantes con clasificación bloqueante/no bloqueante
- [ ] Tests unitarios para cada adapter

## Recurso de datos involucrado
### Recurso
- **Nombre:** SensorReading
- **Capa(s):** backend

### Campos del recurso
| Campo | Tipo | Requerido | Descripción / Restricciones |
|---|---|---|---|
| id | UUID | Sí | Identificador único |
| finca_id | UUID | Sí | FK a Finca |
| ts | Timestamp | Sí | Marca de tiempo de la medición |
| ph | Float | No | 0-14 |
| nitrogeno | Float | No | ppm |
| fosforo | Float | No | ppm |
| potasio | Float | No | ppm |
| calcio | Float | No | ppm |
| magnesio | Float | No | ppm |
| azufre | Float | No | ppm |
| hierro | Float | No | ppm |
| manganeso | Float | No | ppm |
| zinc | Float | No | ppm |
| cobre | Float | No | ppm |
| boro | Float | No | ppm |
| materia_organica | Float | No | porcentaje |
| cic | Float | No | meq/100g |
| textura | Enum(Arena/Limo/Arcilla) | No | Clasificación textural |
| humedad | Float | No | porcentaje |
| temperatura_suelo | Float | No | °C |
| conductividad_electrica | Float | No | dS/m |

## Dependencias
TT-07 (modelo de datos)
