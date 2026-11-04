# Consultas, índices y planes de ejecución

## Tabla de contenido

1. Reglas de oro
2. Diseño de índices
3. Leer planes por motor
4. Patrones de aplicación (ORM)
5. Diagnóstico de lentitud

## 1. Reglas de oro

- **SARGabilidad:** nada de funciones ni conversiones sobre columnas indexadas en
  `WHERE`/`JOIN`. `WHERE created_at >= :d AND created_at < :d2` en vez de
  `YEAR(created_at) = 2026`; tipos iguales a ambos lados (`cuenta_id = 1050`, no `'1050'`).
  Si la función es inevitable, índice de expresión/función.
- **Proyección explícita:** sin `SELECT *` en código de aplicación (habilita índices
  cubrientes y evita traer columnas grandes o sensibles).
- **Paginación por clave (keyset):** `WHERE (fecha, id) < (:f, :id) ORDER BY fecha DESC, id
  DESC LIMIT 50`; `OFFSET` profundo lee y descarta filas.
- **Límite siempre:** toda consulta de lista en ruta de usuario tiene tope.
- **`EXISTS` en vez de `COUNT(*) > 0`;** `NOT EXISTS` en vez de `NOT IN` con subconsulta
  que puede tener `NULL`.
- **`OR` entre columnas distintas** puede impedir índices: `UNION ALL` o índices separados.
- **Parámetros bind siempre** (rendimiento por planes reutilizados y seguridad). Cuidado
  con *parameter sniffing* (SQL Server) y planes genéricos (PG `plan_cache_mode`).

## 2. Diseño de índices

- Compuesto: igualdad primero, luego orden, luego rango (ESR); el prefijo izquierdo
  manda.
- Cubriente (`INCLUDE` en PG 11+/SQL Server) para consultas calientes.
- Parcial/filtrado para subconjuntos frecuentes (`WHERE estado = 'PENDIENTE'`).
- Cada índice cuesta en escritura, almacenamiento y vacuum: justifica por patrón de
  acceso; elimina duplicados y no usados (con evidencia de estadísticas de uso de un
  periodo representativo, incluido cierre de mes).
- Tipos especiales: GIN (jsonb, arrays, full-text), GiST/SP-GiST (rangos, geo), BRIN
  (series ordenadas enormes), hash; Oracle bitmap (solo DW), function-based; SQL Server
  columnstore (analítico).
- FK con índice (ver modelado relacional).

## 3. Leer planes por motor

| Motor | Comando | Mira |
|---|---|---|
| PostgreSQL | `EXPLAIN (ANALYZE, BUFFERS, SETTINGS)` (ANALYZE ejecuta: solo en copia o con `BEGIN; ... ROLLBACK;` para DML) | Seq Scan sobre tablas grandes, filas estimadas vs reales, `Rows Removed by Filter`, sorts a disco, nested loop con muchas filas |
| Oracle | `EXPLAIN PLAN FOR` + `DBMS_XPLAN.DISPLAY`; real: `DBMS_XPLAN.DISPLAY_CURSOR(format=>'ALLSTATS LAST')` | `TABLE ACCESS FULL`, cardinalidades E-Rows vs A-Rows, `INDEX FULL SCAN` inesperado |
| SQL Server | Plan real (`SET STATISTICS XML ON`), Query Store | Scans, key lookups masivos, advertencias de conversión implícita, spills |
| MySQL | `EXPLAIN FORMAT=TREE` / `EXPLAIN ANALYZE` (8.0.18+) | `type: ALL`, `Using filesort`, `Using temporary`, `rows` alto |
| MongoDB | `explain("executionStats")` | `COLLSCAN`, `totalDocsExamined` ≫ `nReturned` |
| DynamoDB | Métricas de `ConsumedCapacity` y `ScannedCount` vs `Count` | `Scan`, `FilterExpression` que descarta mucho |

Una estimación muy distinta de la real apunta a estadísticas desactualizadas o
correlaciones no modeladas, no necesariamente a un índice faltante.

## 4. Patrones de aplicación (ORM)

- **N+1:** relaciones perezosas recorridas en bucle (JPA `@OneToMany` LAZY en un `for`,
  repositorios por ítem en Go). Usa fetch join/`@EntityGraph`, consultas por lote (`IN`
  acotado) o proyecciones.
- **EAGER por defecto** en `@ManyToOne` de JPA trae grafos enormes: márcalo LAZY y trae
  explícitamente.
- **`findAll()` / sin paginación** en repositorios usados por endpoints.
- **Reactivo (R2DBC):** sin `.block()`; `Flux` con `limitRate`/paginación; transacciones con
  `TransactionalOperator`.
- **Batch:** inserciones por lote (`saveAll` con `hibernate.jdbc.batch_size` y IDs que no
  rompan el batching; `COPY`/`pgx.CopyFrom`; `BULK INSERT`), commits por lotes acotados.
- **Conteos totales** en cada página: costosos en tablas grandes; ofrece "hay más".

## 5. Diagnóstico de lentitud (solo lectura)

1. Identifica la consulta y su frecuencia/latencia (pg_stat_statements, AWR/ASH,
   Query Store, Performance Schema, Performance Insights, profiler de Mongo).
2. Obtén el plan real en copia o con lectura segura.
3. Revisa esperas/bloqueos (pg_locks + pg_stat_activity, `v$session`, `sys.dm_os_waiting_tasks`,
   `performance_schema.data_locks`).
4. Revisa estadísticas, bloat, configuración de memoria de trabajo.
5. Propón el cambio mínimo (reescritura, índice, estadística) con el plan esperado y cómo
   medir la mejora. La creación de índices en producción sigue las reglas de migración.
