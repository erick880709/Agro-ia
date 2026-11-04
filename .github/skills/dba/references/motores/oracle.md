# Oracle Database (incluye RDS for Oracle, Exadata/OCI, APEX)

Contexto frecuente en banca (sistemas PL/SQL y APEX existentes). Verifica versión
(19c LTS, 21c, 23ai) y edición (EE vs SE2: `ONLINE`, particionamiento y compresión
avanzada requieren EE y, algunos, opciones licenciadas).

## Tabla de contenido
1. Diseño · 2. Índices y planes · 3. Concurrencia · 4. PL/SQL · 5. DDL en línea ·
6. HA/DR · 7. Seguridad · 8. Diagnóstico

## 1. Diseño
- `NUMBER(p,s)` para numéricos; `VARCHAR2(n CHAR)` con semántica de caracteres en UTF-8;
  `TIMESTAMP WITH TIME ZONE` para instantes (el `DATE` incluye hora, sin zona).
- `''` = `NULL`. Identity columns (12c+) o secuencias con `CACHE` adecuado (no `NOCACHE`
  en alto volumen; en RAC considera `NOORDER`).
- `BOOLEAN` SQL y `IF [NOT] EXISTS` en DDL solo en 23ai.
- Particionamiento (licencia): rango/intervalo por fecha, lista, hash; índices locales vs globales.

## 2. Índices y planes
- B-tree; function-based para expresiones; bitmap solo en DW (bloquea en OLTP).
- Planes: `DBMS_XPLAN.DISPLAY_CURSOR(NULL, NULL, 'ALLSTATS LAST')` con
  `/*+ GATHER_PLAN_STATISTICS */` en copia; SQL Plan Baselines para estabilizar; evitar
  hints como solución permanente.
- Estadísticas con `DBMS_STATS` (histogramas en columnas sesgadas; cuidado con bind peeking).

## 3. Concurrencia
- Lectores no bloquean escritores (undo). ORA-01555 por transacciones/consultas largas
  con undo insuficiente.
- `SELECT ... FOR UPDATE [NOWAIT|SKIP LOCKED]`; FK sin índice provoca bloqueos de tabla
  del hijo al modificar el padre.
- ORA-00060 (deadlock): trace en alert log.

## 4. PL/SQL
- Paquetes con especificación estable; `BULK COLLECT ... LIMIT` + `FORALL`; sin commits en
  bucles; `RAISE_APPLICATION_ERROR(-20xxx, ...)`; nada de `WHEN OTHERS THEN NULL`.
- `EXECUTE IMMEDIATE ... USING`; `DBMS_ASSERT` para identificadores.
- `AUTHID CURRENT_USER` vs `DEFINER` decidido explícitamente.
- Pruebas con utPLSQL. APEX: lógica en paquetes, no en procesos de página.

## 5. DDL en línea
`CREATE INDEX ... ONLINE`, `ALTER TABLE ... MOVE ONLINE` (12.2+), `DBMS_REDEFINITION`,
`ADD COLUMN ... DEFAULT ... NOT NULL` como metadato; DDL hace commit implícito;
recompilar objetos inválidos tras cambios.

## 6. HA/DR
RMAN (incremental + archivelog, `VALIDATE`), Flashback (table/query/database) para errores
lógicos, Data Guard (modos Max Performance/Availability/Protection), RAC para HA local
(no es DR). RDS: Multi-AZ, réplicas, backups automáticos.

## 7. Seguridad
Unified Auditing, VPD/RAS para aislamiento por fila, TDE (Advanced Security), Data
Redaction, perfiles de contraseña, sin `GRANT ANY` a aplicaciones, esquema dueño
bloqueado (`ACCOUNT LOCK`) y usuario de aplicación separado con sinónimos/grants mínimos.

## 8. Diagnóstico (solo lectura)
```sql
-- Top SQL por tiempo (requiere privilegios sobre v$; AWR/ASH requieren Diagnostics Pack)
SELECT sql_id, executions, ROUND(elapsed_time/1e6/NULLIF(executions,0),3) seg_por_exec,
       buffer_gets, SUBSTR(sql_text,1,100) FROM v$sql ORDER BY elapsed_time DESC FETCH FIRST 20 ROWS ONLY;
-- Sesiones bloqueadas
SELECT sid, serial#, blocking_session, event, seconds_in_wait, sql_id FROM v$session WHERE blocking_session IS NOT NULL;
-- Objetos inválidos
SELECT owner, object_type, object_name FROM dba_objects WHERE status = 'INVALID';
```
