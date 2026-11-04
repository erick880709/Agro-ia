# Migraciones de esquema seguras

Basado en `write-safe-migrations` (antonrisch), `database-migrations` (ECC) y las guías
de PostgreSQL de Neon/Microsoft, adaptado a Flyway/Liquibase (Java/Scaffold),
golang-migrate/goose/Atlas (Go) y a los motores del banco.

## Tabla de contenido

1. Principios
2. Expand → migrate → contract
3. Operaciones peligrosas por motor
4. Backfill por lotes
5. Herramientas de migración
6. Pruebas y CI
7. Rollback y verificación

## 1. Principios

- Cada migración es incremental, versionada, revisada y **nunca se edita una vez aplicada**
  en un ambiente compartido (rompe checksums de Flyway/Liquibase y la reproducibilidad).
- El esquema debe ser compatible con **la versión anterior y la nueva de la aplicación**
  durante el despliegue (rolling/blue-green).
- Separar DDL y DML masivo; separar migraciones que no pueden ir en transacción
  (`CREATE INDEX CONCURRENTLY`).
- Conocer el lock que toma cada operación y el tamaño real de la tabla; fijar
  `lock_timeout` para fallar rápido en lugar de encolar a todos detrás.
- Una reversión que borra datos no es rollback; el rollback real suele ser *roll forward*.

## 2. Expand → migrate → contract

| Cambio | Expand | Migrate | Contract |
|---|---|---|---|
| Renombrar columna | Añadir nueva nullable; app escribe ambas | Backfill por lotes; app lee la nueva | Quitar escritura vieja; eliminar columna en release posterior |
| Cambiar tipo (INT→BIGINT) | Nueva columna BIGINT + trigger o doble escritura | Backfill; validar; cambiar PK/FK con cuidado | Swap y eliminar vieja |
| Volver obligatoria | Default/escritura en la app | Backfill nulos | PG: `CHECK (col IS NOT NULL) NOT VALID` → `VALIDATE` → `SET NOT NULL` (PG 12+ usa el check) |
| Nueva FK | — | Limpiar huérfanos | PG: `ADD CONSTRAINT ... NOT VALID` → `VALIDATE CONSTRAINT`; Oracle: `ENABLE NOVALIDATE` → `VALIDATE`; SQL Server: `WITH NOCHECK` → `CHECK CONSTRAINT` (no confiable hasta validar) |
| Eliminar tabla/columna | App deja de usarla (release N) | Respaldo/archivo si aplica | Eliminar en release N+1 |

## 3. Operaciones peligrosas por motor

**PostgreSQL**
- `CREATE INDEX` sin `CONCURRENTLY` bloquea escrituras; `CONCURRENTLY` no corre en
  transacción y puede dejar índice `INVALID` (verificar `pg_index.indisvalid`).
- `ALTER COLUMN TYPE` reescribe la tabla (salvo casos binario-compatibles, p. ej.
  ampliar `varchar`).
- `ADD COLUMN ... DEFAULT <volátil>` reescribe; con constante es solo metadato desde PG 11.
- `SET NOT NULL` escanea con `ACCESS EXCLUSIVE` (ver patrón con `CHECK NOT VALID`).
- `VACUUM FULL`, `CLUSTER`, `REINDEX` sin `CONCURRENTLY` (PG 12+), `LOCK TABLE`.
- Cualquier `ALTER TABLE` necesita `ACCESS EXCLUSIVE` aunque sea breve: con transacciones
  largas en curso se encola y bloquea a todos → `SET lock_timeout = '5s'`.

**Oracle**
- `CREATE INDEX ... ONLINE` (Enterprise) para no bloquear DML; `ALTER TABLE ... MOVE ONLINE`
  (12.2+); redefinición online con `DBMS_REDEFINITION` para cambios grandes.
- Añadir columna `NOT NULL` con `DEFAULT` es metadato desde 11g/12c; sin default falla con filas.
- DDL hace commit implícito: no mezcles con DML que esperas revertir.
- Invalidación de objetos PL/SQL dependientes tras DDL: recompilar y verificar
  `user_objects WHERE status = 'INVALID'`.

**SQL Server**
- `CREATE INDEX ... WITH (ONLINE = ON)` (Enterprise/Azure SQL); `RESUMABLE = ON` en
  versiones soportadas.
- Añadir columna `NOT NULL` con default constante es metadato (Enterprise 2012+);
  cambiar tipo reescribe.
- Usar `WAIT_AT_LOW_PRIORITY` en operaciones online para no bloquear a todos.

**MySQL/MariaDB**
- Especifica `ALGORITHM=INSTANT|INPLACE, LOCK=NONE` para que falle si no es posible en
  vez de copiar la tabla en silencio; tablas grandes con `gh-ost`/`pt-online-schema-change`.
- Cuidado con replicación: DDL largos generan lag en réplicas.

**NoSQL**
- DynamoDB: cambiar la clave primaria exige tabla nueva + migración; GSI nuevo hace
  backfill que consume capacidad.
- MongoDB: índices se construyen sin bloquear la colección desde 4.2 pero consumen
  recursos; cambios de forma de documento con versionado de esquema (`schemaVersion`) y
  migración perezosa o por lotes.
- Cassandra/ScyllaDB: no se cambia la clave primaria; tabla nueva + doble escritura +
  backfill.

## 4. Backfill por lotes

- Lotes por rango de clave (no `OFFSET`), tamaño ajustado para transacciones cortas
  (p. ej. 1–10 k filas), pausa entre lotes, idempotente (`WHERE nueva IS NULL`), reanudable,
  con monitoreo de lag de réplicas y bloqueos.
- Fuera de la migración versionada si dura más que el despliegue (job controlado).

## 5. Herramientas de migración

| Stack | Herramienta | Notas |
|---|---|---|
| Java/Spring, Scaffold | Flyway (`db/migration/V<n>__<desc>.sql`) o Liquibase (changelog) | para `CONCURRENTLY`, script config `V<n>__x.sql.conf` con `executeInTransaction=false` (o `mixed` según versión: verifica el comportamiento de la versión del proyecto); `validateOnMigrate` activo; `outOfOrder` desactivado en prod |
| Go | golang-migrate, goose, Atlas, tern | Archivos `up`/`down`; Atlas con lint de migraciones (`atlas migrate lint`) |
| Node/TS | Prisma, Drizzle, Knex, TypeORM | `prisma migrate deploy` en prod; nunca `db push` en prod |
| Python | Alembic, Django | Revisar autogenerados |
| Linters | `squawk` (PG), `atlas migrate lint`, `scripts/migration_lint.py` | Candidatos, no veredictos |

## 6. Pruebas y CI

- Aplicar migraciones desde cero y desde la versión de producción en una base efímera
  (Testcontainers, contenedor en CI) y ejecutar tests de integración.
- Probar con volumen representativo las migraciones sobre tablas grandes (tiempos y locks).
- Verificar compatibilidad: tests de la versión N-1 de la app contra el esquema nuevo
  cuando haya despliegue gradual.

## 7. Rollback y verificación

Cada plan declara: punto de no retorno, cómo volver antes de él, respaldo (snapshot o
PITR verificado antes de cambios destructivos), consultas de verificación (conteos,
nulos, huérfanos, `indisvalid`, objetos inválidos), métricas a vigilar (bloqueos, lag,
errores, latencia) y criterio de avance a la siguiente fase.
