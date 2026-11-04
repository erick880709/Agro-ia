# MySQL / MariaDB (incluye Aurora MySQL, RDS, Azure Database for MySQL)

## Tabla de contenido
1. Diseño · 2. Índices y planes · 3. Concurrencia · 4. DDL en línea · 5. Replicación · 6. Diagnóstico

## 1. Diseño
- InnoDB siempre; `utf8mb4` (no `utf8`/`utf8mb3`) con collation explícita.
- PK clusterizada: `BIGINT AUTO_INCREMENT` o UUID ordenado en `BINARY(16)`
  (`UUID_TO_BIN(uuid, 1)`); UUID aleatorio fragmenta.
- `DATETIME` (sin conversión de zona, hasta 9999) vs `TIMESTAMP` (UTC, límite 2038):
  decide y documenta; `DECIMAL` para dinero.
- `sql_mode` estricto (`STRICT_TRANS_TABLES`, `ONLY_FULL_GROUP_BY`).

## 2. Índices y planes
- Prefijo izquierdo; índices de prefijo para textos largos; índices invisibles (8.0) para
  probar eliminación; `EXPLAIN ANALYZE` (8.0.18+).
- Sin índices de función antes de 8.0.13 (usar columnas generadas).

## 3. Concurrencia
REPEATABLE READ con gap/next-key locks: `SELECT ... FOR UPDATE` sobre rangos sin índice
bloquea de más; deadlocks en `SHOW ENGINE INNODB STATUS`.

## 4. DDL en línea
`ALGORITHM=INSTANT` (8.0.12+; añadir columna al final, más casos en 8.0.29+),
`ALGORITHM=INPLACE, LOCK=NONE` explícitos para fallar si no es posible; tablas grandes con
`gh-ost` o `pt-online-schema-change`; DDL largo genera lag en réplicas.

## 5. Replicación
GTID, binlog en formato `ROW`, réplicas con lag monitorizado; Aurora: réplicas de
almacenamiento compartido, Global Database para DR.

## 6. Diagnóstico (solo lectura)
```sql
SELECT digest_text, count_star, ROUND(avg_timer_wait/1e9,2) AS ms_prom
FROM performance_schema.events_statements_summary_by_digest ORDER BY sum_timer_wait DESC LIMIT 20;
SELECT * FROM sys.schema_unused_indexes;
SELECT * FROM performance_schema.data_lock_waits;
```
