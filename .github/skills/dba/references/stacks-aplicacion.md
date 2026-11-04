# Acceso a datos por stack de aplicación

Complementa los perfiles de builder (`stacks/java-spring`, `stacks/go`, `stacks/angular`)
y la guía reactiva de code-review. El stack del proyecto manda; aquí está lo que un DBA
revisa en el código que habla con la base.

## Tabla de contenido

1. Java / Spring y Scaffold Bancolombia
2. Go
3. Frontend (Angular)
4. Pruebas con base de datos real

## 1. Java / Spring y Scaffold Bancolombia

**Driven adapters de datos del Scaffold** (`gradle gda --type=<t>`): `jpa` (con
`--secret=true` para credenciales vía Secrets Manager), `r2dbc` (cliente PostgreSQL
reactivo), `mongodb`, `dynamodb`, `redis` (`--mode=template|repository`). Reglas:
- El acceso a datos vive en el driven adapter; el dominio solo conoce el gateway
  (interfaz). Entidades de persistencia ≠ modelos de dominio (mapeo explícito); no filtres
  anotaciones JPA/Mongo al `domain/model`.
- No generes ni ajustes esquemas con `spring.jpa.hibernate.ddl-auto=update|create` fuera de
  desarrollo local: las migraciones (Flyway/Liquibase) son la fuente de verdad. En prod
  `validate` o `none`.
- `open-in-view` desactivado (`spring.jpa.open-in-view=false`) para evitar consultas
  perezosas fuera de la capa y conexiones retenidas.

**JPA/Hibernate:**
- Relaciones `LAZY` por defecto; fetch explícito (`JOIN FETCH`, `@EntityGraph`) por caso de uso.
- `@Version` para bloqueo optimista en agregados con edición concurrente.
- Batch: `hibernate.jdbc.batch_size`, `order_inserts/updates`; `GenerationType.IDENTITY`
  deshabilita el batching de inserts en Hibernate → secuencia con `allocationSize`
  alineado al `INCREMENT BY`.
- `@Transactional(readOnly = true)` en lecturas; transacciones en el caso de uso/adapter
  según convención, nunca en el controller por conveniencia.
- Consultas nativas: parámetros nombrados, nunca concatenación.

**R2DBC / WebFlux:**
- Nada de JDBC ni `.block()` en el event loop; pool `r2dbc-pool` dimensionado.
- Transacciones reactivas con `TransactionalOperator` o `@Transactional` sobre
  `ReactiveTransactionManager`; recuerda que el contexto transaccional viaja en el
  `Context` de Reactor.
- Streaming de resultados grandes con backpressure (`limitRate`), no `collectList()` de
  tablas completas.

**DynamoDB / Mongo / Redis (adapters):**
- DynamoDB Enhanced Client con `Query` por clave, `ConditionExpression` para invariantes,
  paginación por `LastEvaluatedKey`; prohibido `scan()` en ruta de usuario.
- Mongo: índices declarados (no `auto-index-creation` en prod), proyecciones, `writeConcern`.
- Redis: TTL en todas las claves de caché, sin `KEYS`, serialización versionada.

**Pool HikariCP:** ver [transacciones y conexiones](transacciones-y-concurrencia.md) §5.

## 2. Go

- `database/sql` o `pgx`/`pgxpool`; `sqlc` para consultas tipadas (revisa el SQL fuente,
  no el código generado).
- Siempre `QueryContext`/`ExecContext` con `context` con timeout; `rows.Close()` y
  `rows.Err()`; `defer tx.Rollback()` tras `BeginTx` (no-op si hubo commit).
- Placeholders (`$1`, `?`); nunca `fmt.Sprintf` para SQL.
- `SetMaxOpenConns`, `SetMaxIdleConns`, `SetConnMaxLifetime`/`MaxConnLifetime`.
- Bulk: `pgx.CopyFrom`; lotes con `pgx.Batch`.
- Migraciones con golang-migrate/goose/Atlas; `embed` de archivos SQL.
- DynamoDB SDK v2: `Query` con `KeyConditionExpression`, `Paginator`, expresiones con
  `expression` builder.

## 3. Frontend (Angular)

El frontend no accede a la base. Revisa solo que la paginación, filtros y ordenamientos
que pide sean servibles por la API con índices (p. ej. ordenar por cualquier columna
desde una tabla del UI implica índices o límites en backend).

## 4. Pruebas con base de datos real

- Integración con el motor real (Testcontainers para PostgreSQL/Oracle Free/SQL Server/
  MySQL/Mongo, DynamoDB Local o LocalStack) aplicando las migraciones del proyecto; H2 no
  prueba el dialecto ni los bloqueos reales.
- Pruebas de concurrencia para invariantes críticos (dos transacciones simultáneas sobre
  el mismo saldo/clave de idempotencia).
- Datos sintéticos; nunca copias de producción sin anonimizar.
