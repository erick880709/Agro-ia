# Transacciones, concurrencia y conexiones

## Tabla de contenido

1. Niveles de aislamiento por motor
2. Anomalías y cómo prevenirlas
3. Idempotencia, outbox y efectos externos
4. Bloqueos y deadlocks
5. Pools de conexión

## 1. Niveles de aislamiento por motor

| Motor | Por defecto | Notas |
|---|---|---|
| PostgreSQL | READ COMMITTED | `REPEATABLE READ` = snapshot; `SERIALIZABLE` (SSI) exige reintentar `40001` |
| Oracle | READ COMMITTED | `SERIALIZABLE` lanza ORA-08177; lecturas nunca bloquean escrituras |
| SQL Server | READ COMMITTED (con bloqueos) | Considera `READ_COMMITTED_SNAPSHOT ON` para reducir bloqueos lector/escritor; `SNAPSHOT` con conflictos de actualización |
| MySQL InnoDB | REPEATABLE READ | Gap/next-key locks; `SELECT ... FOR UPDATE` bloquea rangos |
| MongoDB | Por operación; transacciones con snapshot | `writeConcern: majority`, `readConcern` acorde |
| DynamoDB | Ítem atómico; transacciones serializables acotadas | Escrituras condicionales para invariantes |

## 2. Anomalías y cómo prevenirlas

- **Lost update / saldo:** "leer saldo → calcular → escribir" en READ COMMITTED pierde
  actualizaciones. Usa `UPDATE cuentas SET saldo = saldo - :m WHERE id = :id AND saldo >= :m`
  (atómico y condicional), `SELECT ... FOR UPDATE`, bloqueo optimista con versión
  (`@Version` en JPA, `version` condicional en NoSQL) o SERIALIZABLE con reintento.
- **Write skew:** dos transacciones validan una condición sobre filas distintas; requiere
  SERIALIZABLE, bloqueo explícito del recurso común o una restricción.
- **Unicidad bajo concurrencia:** solo una restricción `UNIQUE` (o escritura condicional)
  la garantiza; "verificar que no existe y luego insertar" no.
- **Reintentos:** solo con transacción completa repetible y backoff con jitter; maneja
  serialización (`40001`), deadlock (`40P01`, 1205, ORA-00060) y timeouts de forma distinta
  a errores de negocio.

## 3. Idempotencia, outbox y efectos externos

- Clave de idempotencia persistida con `UNIQUE` en la misma transacción que el efecto.
- No llames APIs externas ni publiques eventos dentro de una transacción de BD abierta;
  usa **outbox transaccional** (tabla `outbox` en la misma transacción + relay/CDC con
  Debezium o el mecanismo del proyecto) para no publicar eventos de cambios revertidos ni
  perder eventos de cambios confirmados.
- Consumidores idempotentes (tabla de mensajes procesados o upsert condicional).

## 4. Bloqueos y deadlocks

- Transacciones cortas; nada de interacción humana o red dentro.
- Orden consistente de acceso a recursos para evitar deadlocks.
- `lock_timeout`/`statement_timeout` (PG), `LOCK_TIMEOUT` (SQL Server),
  `innodb_lock_wait_timeout` (MySQL) configurados en migraciones y operaciones largas.
- Triage de deadlocks: grafo (SQL Server `system_health`/XE, PG log con
  `log_lock_waits`, Oracle trace de ORA-00060, MySQL `SHOW ENGINE INNODB STATUS`),
  identificar recursos y orden, corregir con índice (evita escaneos que bloquean de más)
  u orden consistente.

## 5. Pools de conexión

- Tamaño del pool por instancia × instancias/pods ≤ conexiones disponibles del motor menos
  reserva administrativa. En Kubernetes con HPA calcula con el máximo de réplicas.
- HikariCP: tamaño pequeño (el rendimiento cae con pools grandes), `maxLifetime` menor que
  timeouts del servidor/proxy, `connectionTimeout` acotado. R2DBC: `r2dbc-pool` con
  `maxSize` y `maxIdleTime`. Go: `SetMaxOpenConns`, `SetMaxIdleConns`, `SetConnMaxLifetime`
  (o `pgxpool`).
- Proxy/pooler: PgBouncer (modo transacción incompatible con prepared statements de
  sesión en versiones antiguas; revisa la versión), RDS Proxy, Azure PgBouncer
  integrado. Lambdas/serverless casi siempre necesitan proxy.
- Timeouts de consulta en la aplicación y en la base; cancelación propagada (`context` en
  Go, timeouts reactivos).
