# RD-011: Modelo de datos ampliado (sensor y calibración)

**Tipo:** Información de diseño
**Fuente:** RFP-AGROIA-003 §8 y §11

## Descripción
Cambios al esquema: `sensor_readings` suma `valor_crudo`, `valor_escalado`, `valor_normalizado`, `unidad`, `incertidumbre`, `calidad` (enum ampliado), `motivos_calidad[]`, `version_regla`, `grado_evidencia`, `profundidad_cm`, `punto_id`, `replica_n`, `sesion_muestreo_id`, `vwc_pct`, `ce_25c_dsm`. `dispositivos_iot` suma `modelo`, `variante`, `direccion_modbus`, `baudios`, `firmware`, `fecha_instalacion`, `profundidad_cm`, `modo_instalacion`, `lote_id`, `ultimo_mantenimiento`, `estado_salud`. Nuevas tablas: `calibracion_sensor` (dispositivo, variable, unidad de suelo, pendiente, intercepto, n, R², RMSE, sesgo, vigencia), `par_calibracion` (lectura sensor + resultado laboratorio con método), `sesion_muestreo` (punto, réplicas, contexto de fertilización y riego, observaciones), `parametro_calidad_sensor` (parámetros administrables con versión).

## Elementos de referencia
Entidades y columnas descritas arriba; diagrama a construir en el kickoff.

## Notas del analista
Migraciones Alembic reversibles (RNF-034); enum `calidad` ampliado respecto al actual.
