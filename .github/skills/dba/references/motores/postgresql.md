# PostgreSQL (incluye Aurora/RDS, Azure Flexible Server, Cloud SQL)

Basado en `postgres-best-practices` (Neon, PG 14–18), `postgresql-best-practices`
(Microsoft) y `pg-mastery`. Verifica la versión: PG 14 sale de soporte en noviembre de 2026.

## Tabla de contenido
1. Diseño · 2. Índices · 3. Concurrencia y MVCC · 4. Mantenimiento · 5. Particionamiento ·
6. Replicación y HA · 7. Seguridad · 8. Administrados · 9. Diagnóstico

## 1. Diseño
- `bigint generated always as identity` o `uuid` (UUIDv7 para localidad; `uuidv7()` [PG18+]).
- `timestamptz`, `numeric(p,s)`, `text` + `CHECK` de longitud si es regla; `jsonb` (no
  `json`) con GIN solo si se consulta por contenido.
- Esquemas por bounded context; `search_path` explícito en funciones `SECURITY DEFINER`.
- `MERGE` [PG15+], `NULLS NOT DISTINCT` en unique [PG15+], `json_table` [PG17+].

## 2. Índices
- B-tree por defecto; `INCLUDE` para cubrientes; parciales (`WHERE`); de expresión.
- GIN (`jsonb_path_ops` si solo `@>`), GiST (rangos, `EXCLUDE`), BRIN (series enormes
  ordenadas físicamente), `pg_trgm` para `LIKE '%x%'`.
- `CREATE INDEX CONCURRENTLY` en producción; `REINDEX CONCURRENTLY` [PG12+].
- FK sin índice: detectar con consulta sobre `pg_constraint` vs `pg_index`.

## 3. Concurrencia y MVCC
- Transacciones largas impiden vacuum (bloat) y retienen locks: `idle_in_transaction_session_timeout`.
- `SELECT ... FOR UPDATE SKIP LOCKED` para colas de trabajo.
- `SERIALIZABLE` requiere reintento en `40001`.
- Locks de DDL: `SET lock_timeout` en migraciones.

## 4. Mantenimiento
- Autovacuum por tabla grande (`autovacuum_vacuum_scale_factor` bajo, `cost_limit`);
  monitor `n_dead_tup`, `last_autovacuum`, wraparound (`age(datfrozenxid)`).
- `ANALYZE` tras cargas masivas y upgrades; estadísticas extendidas (`CREATE STATISTICS`)
  para columnas correlacionadas.
- `VACUUM FULL` bloquea: preferir `pg_repack` si se dispone y es aprobado.

## 5. Particionamiento
- Declarativo por rango (fecha) o lista (tenant/región) para tablas grandes con
  retención por tiempo: `DETACH PARTITION CONCURRENTLY` [PG14+] + drop para purgar.
- La clave de partición debe estar en las consultas calientes y en PK/unique.
- `pg_partman` para crear particiones futuras (si está permitido en el servicio).

## 6. Replicación y HA
- Streaming (física) para HA/lectura; lógica para migraciones, upgrades y CDC (tablas
  con PK o `REPLICA IDENTITY`).
- Slots de replicación abandonados retienen WAL hasta llenar disco: monitorear `pg_replication_slots`.

## 7. Seguridad
- Roles: dueño del esquema (migraciones), app (DML), lectura. `REVOKE CREATE ON SCHEMA
  public FROM PUBLIC` (por defecto desde PG15).
- RLS con `FORCE` y `current_setting('app.tenant_id')` fijado por la app; pgAudit.
- `scram-sha-256`; TLS `verify-full`.

## 8. Administrados
- RDS/Aurora: parameter groups, `rds_superuser`, RDS Proxy, Performance Insights,
  blue/green para upgrades, Aurora I/O-Optimized según perfil.
- Azure Flexible Server: `az postgres flexible-server parameter set`, `azure_pg_admin`,
  PgBouncer integrado, Entra ID auth, PITR crea servidor nuevo.
- Nunca `ALTER SYSTEM`, archivos `pg_hba.conf`/`postgresql.conf` ni comandos de SO.

## 9. Diagnóstico (solo lectura)
```sql
-- Top consultas (requiere pg_stat_statements)
SELECT queryid, calls, round(mean_exec_time::numeric,2) AS ms_prom, rows, left(query,120)
FROM pg_stat_statements ORDER BY total_exec_time DESC LIMIT 20;
-- Bloqueos actuales
SELECT a.pid, a.state, a.wait_event_type, a.wait_event, pg_blocking_pids(a.pid) AS bloqueado_por,
       now()-a.xact_start AS duracion_tx, left(a.query,100)
FROM pg_stat_activity a WHERE a.wait_event_type = 'Lock' OR now()-a.xact_start > interval '5 min';
-- Índices no usados (validar con un periodo representativo)
SELECT s.relname, s.indexrelname, s.idx_scan, pg_size_pretty(pg_relation_size(s.indexrelid))
FROM pg_stat_user_indexes s JOIN pg_index i ON i.indexrelid = s.indexrelid
WHERE s.idx_scan = 0 AND NOT i.indisunique ORDER BY pg_relation_size(s.indexrelid) DESC;
```
