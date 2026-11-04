# Revisión de datos y persistencia (pasada H)

Aplica cuando el diff toca migraciones (`db/migration`, changelogs, `*.up.sql`), DDL,
entidades/mapeos ORM, repositorios o SQL embebido, procedimientos, configuración de
datasource/pool o IaC de bases de datos.

## 0. Escalamiento a `dba`

Si la skill `dba` está disponible, escala a su modo `gate` cuando:

- hay migraciones sobre tablas existentes, cambios de tipo, `NOT NULL`, FK o índices;
- cambia el modelo de datos, el motor, transacciones/concurrencia o el pool;
- hay NoSQL (DynamoDB, Mongo, Cassandra/Scylla, Redis) con nuevos patrones de acceso;
- la pasada H deja un candidato que requiere volumen, plan de ejecución o versión del
  motor para confirmarse.

`dba` usa la misma escala (`bloqueante`, `mayor`, `menor`, `nit`, `pregunta`): integra
sus `DB-NNN` sin reinterpretarlos y referencia el ID en vez de duplicar la tarjeta. Si
tú ya reportaste el mismo problema, conserva tu ID y añade el `DB-NNN` como evidencia.
No apruebes con un `DB-NNN` `bloqueante` o `mayor` abierto.

## 1. Mínimo cuando `dba` no está disponible

- **Migraciones:** nunca editar una ya aplicada; sin `DROP`/rename sin expand/contract;
  índices en línea (`CONCURRENTLY`, `ONLINE`, `ALGORITHM=INPLACE`) en tablas grandes;
  `NOT NULL`/FK con estrategia de validación; DDL y backfill masivo separados.
- **Integridad:** invariantes en restricciones (`UNIQUE`, `CHECK`, FK), no en
  "verificar y luego insertar"; dinero en tipo exacto; instantes con zona.
- **Consultas:** sin `SELECT *`, sin funciones sobre columnas indexadas, paginación
  acotada, sin N+1 (`EAGER`, bucles de repositorio), sin `findAll()` en endpoints,
  parámetros bind.
- **Transacciones:** actualización atómica o bloqueo/versión para saldos y contadores;
  idempotencia con `UNIQUE`; nada de llamadas externas dentro de la transacción (outbox).
- **Reactivo:** sin `.block()` ni JDBC en el event loop.
- **Configuración:** `ddl-auto` en `validate`/`none` fuera de local; pool dimensionado
  contra conexiones del motor × réplicas.
- **NoSQL:** sin `Scan`/`ALLOW FILTERING`/`KEYS *` en ruta de usuario; TTL en caché.

Si `diff_triage.py` no marca datos pero ves SQL o migraciones, aplica esta pasada igual.
