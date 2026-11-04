# Apache Cassandra, ScyllaDB y Amazon Keyspaces

Basado en `scylladb/agent-skills` (`scylladb-data-modeling`, `scylladb-alternator`, entre otras).

## Tabla de contenido
1. Modelado · 2. Particiones y tombstones · 3. Consistencia y LWT · 4. Compactación y TTL · 5. Operación

## 1. Modelado
"Empieza por las consultas, no por las entidades": una tabla por consulta, la clave de
partición en cada `WHERE`, clustering para el orden; denormalización aceptada y mantenida
por la aplicación (o batches lógicos de la misma partición). Sin joins; agregados solo
sobre prefijos de clave.

## 2. Particiones y tombstones
- Particiones acotadas (orientativo: decenas a cientos de MB como máximo, idealmente
  menos): bucketing por tiempo (`(sensor_id, dia)`).
- Borrados y TTL generan tombstones; colas implementadas como tablas con borrados
  frecuentes degradan lecturas.
- `ALLOW FILTERING` = escaneo: inaceptable en rutas de usuario. Índices secundarios y
  vistas materializadas con cautela (costos y limitaciones según motor/versión).

## 3. Consistencia y LWT
`LOCAL_QUORUM` para lectura y escritura con RF=3 en multi-DC; LWT (`IF NOT EXISTS`,
`IF <cond>`) para unicidad y compare-and-set de una partición, con costo de latencia;
`SERIAL`/`LOCAL_SERIAL` para la fase Paxos/Raft según motor.

## 4. Compactación y TTL
STCS para escritura intensiva general, LCS para lectura intensiva con actualizaciones, TWCS
para series de tiempo con TTL uniforme; ScyllaDB ofrece además ICS. Evitar mezclar TTL
distintos en tablas TWCS.

## 5. Operación
Repairs regulares (o servicio administrado que los gestione), monitoreo de latencias p99,
particiones grandes y tombstones; Keyspaces: modelo serverless con límites propios
(sin algunas funciones de Cassandra) — verifica compatibilidad. ScyllaDB Alternator expone
la API de DynamoDB con las mismas reglas de clave.
