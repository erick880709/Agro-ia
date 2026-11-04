# SQL Server (incluye Azure SQL Database/Managed Instance, RDS for SQL Server)

Basado en el libro de skills de SimonBarnett (backups, salud, deadlocks) y prácticas de
T-SQL. Verifica versión y edición (ONLINE/columnstore/particionamiento según edición).

## Tabla de contenido
1. Diseño · 2. Índices y planes · 3. Concurrencia · 4. T-SQL · 5. Backups y HA ·
6. Seguridad · 7. Diagnóstico

## 1. Diseño
- PK clusterizada estrecha, creciente y estable (`BIGINT IDENTITY` o
  `NEWSEQUENTIALID()`); `NEWID()` como clave clusterizada fragmenta.
- `DATETIME2`/`DATETIMEOFFSET`, `DECIMAL(p,s)` (no `MONEY`/`FLOAT`), `NVARCHAR` solo si se
  requiere Unicode; collation consistente entre bases y `tempdb`.
- Temporal tables (system-versioned) para historia.

## 2. Índices y planes
- Índices no clusterizados con `INCLUDE`; filtrados; columnstore para analítica.
- Query Store activo para regresiones de plan; cuidado con *parameter sniffing*
  (`OPTIMIZE FOR`, `RECOMPILE` puntual, PSP optimization en 2022).
- Conversiones implícitas (`VARCHAR` vs `NVARCHAR` desde el driver: JDBC
  `sendStringParametersAsUnicode=false` si las columnas son `VARCHAR`).

## 3. Concurrencia
- `READ_COMMITTED_SNAPSHOT ON` reduce bloqueos lector/escritor (cuesta `tempdb`).
- Deadlocks (1205): capturar grafo desde la sesión XE `system_health`; corregir con índices
  y orden de acceso.
- `SET XACT_ABORT ON` en procedimientos con transacción.

## 4. T-SQL
`TRY...CATCH` + `THROW`; `sp_executesql` parametrizado; set-based sobre cursores; evitar
funciones escalares en columnas de `WHERE` (inlining desde 2019 con limitaciones); tSQLt
para pruebas.

## 5. Backups y HA
- FULL + DIFF + LOG en modelo FULL; `CHECKSUM`, `RESTORE VERIFYONLY` y restauraciones de
  prueba; nombres y retención estandarizados; alertas de jobs fallidos.
- Always On Availability Groups (síncrono para RPO 0 en la región), réplicas legibles,
  `MultiSubnetFailover=True` en la cadena de conexión. Azure SQL: geo-réplica/failover groups.

## 6. Seguridad
Logins contenidos o Entra ID, sin `sa`, roles de base mínimos, TDE, Always Encrypted para
columnas ultra sensibles, Dynamic Data Masking (no es control de seguridad fuerte), SQL
Server Audit, RLS con predicados.

## 7. Diagnóstico (solo lectura)
```sql
-- Top consultas por CPU
SELECT TOP 20 qs.total_worker_time/qs.execution_count AS cpu_prom, qs.execution_count,
       SUBSTRING(st.text, 1, 200) AS texto
FROM sys.dm_exec_query_stats qs CROSS APPLY sys.dm_exec_sql_text(qs.sql_handle) st
ORDER BY qs.total_worker_time DESC;
-- Bloqueos
SELECT session_id, blocking_session_id, wait_type, wait_time, wait_resource
FROM sys.dm_exec_requests WHERE blocking_session_id <> 0;
-- Último backup por base
SELECT d.name, MAX(CASE WHEN b.type='D' THEN b.backup_finish_date END) AS ultimo_full,
       MAX(CASE WHEN b.type='L' THEN b.backup_finish_date END) AS ultimo_log
FROM sys.databases d LEFT JOIN msdb.dbo.backupset b ON b.database_name = d.name GROUP BY d.name;
```
