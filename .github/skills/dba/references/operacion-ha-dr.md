# Operación, HA, DR y capacidad

Basado en las skills de operación de SQL Server (SimonBarnett: estándar de backup,
auditoría de backups, salud de instancia, triage de deadlocks), PostgreSQL (Neon,
Microsoft: hot standby, backup/PITR, upgrades, pooling) y DynamoDB. Todo diagnóstico es
**de solo lectura**; las acciones son propuestas con impacto y requieren confirmación.

## Tabla de contenido

1. RPO/RTO y estrategia de respaldo
2. Alta disponibilidad y réplicas
3. Upgrades y mantenimiento
4. Monitoreo y salud
5. Capacidad y costo
6. Servicios administrados

## 1. RPO/RTO y estrategia de respaldo

| Requisito | Mecanismo típico |
|---|---|
| RPO ≈ minutos | Backups continuos + PITR (WAL/redo/log backups), réplica síncrona o multi-AZ |
| RPO ≈ 0 | Replicación síncrona (multi-AZ, Always On síncrono, Data Guard Max Availability/Protection); con costo de latencia |
| RTO ≈ minutos | Failover automático a standby; DNS/endpoint estable |
| Desastre regional | Réplica cross-región (Aurora Global, Data Guard remoto, geo-réplica Azure, DynamoDB Global Tables) + runbook |
| Error humano/corrupción lógica | PITR, Flashback (Oracle), retención suficiente; **la réplica replica el error** |

- Un backup no restaurado no es un backup: pruebas de restauración periódicas con tiempo
  medido (alimenta el RTO real) y `RESTORE VERIFYONLY`/`pg_verifybackup`/`RMAN VALIDATE`.
- SQL Server: modelo de recuperación FULL en bases con RPO bajo; cadena de log backups
  ininterrumpida; jobs de backup con alertas.
- Retención alineada a regulación y a la necesidad de recuperar errores lógicos.
- Cifrado de backups y copias en otra cuenta/región con acceso restringido (protege
  contra ransomware y borrado malicioso).

## 2. Alta disponibilidad y réplicas

- Réplicas de lectura: la aplicación tolera lag (lecturas de lo propio recién escrito van
  al primario); monitoriza `replica lag`.
- Conflictos en standby (PG `max_standby_streaming_delay`, `hot_standby_feedback` con
  efecto en bloat).
- Failover: los clientes reconectan (pool con validación, DNS TTL bajo, drivers con
  failover: AWS JDBC wrapper, Oracle TAF/ac, `MultiSubnetFailover` en SQL Server).
- NoSQL: factor de replicación y niveles de consistencia (Cassandra/Scylla `LOCAL_QUORUM`),
  `writeConcern majority` en MongoDB, Global Tables con resolución last-writer-wins
  (DynamoDB: diseñar para evitar escrituras concurrentes al mismo ítem en regiones distintas).

## 3. Upgrades y mantenimiento

- Versiones soportadas: planea upgrades antes del fin de soporte (PG 5 años por mayor;
  revisa el calendario del proveedor administrado).
- Upgrade mayor: prueba en copia, revisa incompatibilidades y extensiones, `pg_upgrade`
  o upgrade administrado (blue/green en RDS/Aurora), y luego `ANALYZE`.
- Mantenimiento: autovacuum ajustado por tabla grande (PG), estadísticas (Oracle
  `DBMS_STATS`, SQL Server auto-update + jobs), reconstrucción de índices solo con
  evidencia de fragmentación que afecta (no por calendario ciego), DBCC CHECKDB/`amcheck`.
- Wraparound de XID (PG): monitoriza `age(datfrozenxid)`.

## 4. Monitoreo y salud

Mínimos por motor: conexiones vs máximo, CPU/memoria/IOPS, latencia, consultas top,
esperas/bloqueos, deadlocks, lag de réplicas, espacio libre y crecimiento, backups
exitosos, errores, bloat/fragmentación, cache hit ratio (orientativo). NoSQL: capacidad
consumida y throttling (DynamoDB), particiones grandes y tombstones (Cassandra/Scylla),
`opcounters`/`WiredTiger cache` y oplog window (MongoDB), memoria y evictions (Redis).

## 5. Capacidad y costo

Proyecta crecimiento (filas/día × tamaño de fila × índices × retención), IOPS y
conexiones. En la nube: elige clase/almacenamiento por perfil (I/O-Optimized en Aurora
cuando I/O domina el costo), on-demand vs provisionado en DynamoDB, reservas. Alimenta
`17.4` de archi con supuestos explícitos.

## 6. Servicios administrados

No hay acceso a SO, archivos de configuración ni superusuario: parámetros vía grupos de
parámetros/CLI/portal, roles administrados (`rds_superuser`, `azure_pg_admin`), backups
y réplicas del servicio, extensiones de la lista permitida. Consulta límites del servicio
antes de diseñar (tamaño máximo, conexiones por clase, IOPS).
