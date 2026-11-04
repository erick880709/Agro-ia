# Seguridad de datos (frontera con aegis)

`dba` diseña y revisa controles de datos; `aegis` evalúa explotabilidad. Si encuentras
inyección SQL/NoSQL, IDOR o secretos expuestos, regístralo como handoff a `aegis`.

## Controles

- **Mínimo privilegio:** el usuario de la aplicación no es dueño del esquema; no tiene
  DDL en runtime; roles separados para migración (pipeline), aplicación (DML sobre sus
  tablas), lectura/reporting y administración. Nada de `sa`, `SYSTEM`, `postgres`,
  `root` en aplicaciones. `REVOKE ALL ON SCHEMA public FROM PUBLIC` (PG < 15).
- **Autenticación:** IAM/Entra/Kerberos o credenciales rotadas desde gestor de secretos
  (Scaffold: adapter `secrets`, `--secret=true`); TLS exigido en la conexión
  (`sslmode=verify-full`, `encrypt=true;trustServerCertificate=false`).
- **Aislamiento por fila:** RLS en PostgreSQL (`ENABLE` + `FORCE ROW LEVEL SECURITY` si el
  dueño también consulta), VPD/Real Application Security en Oracle, RLS en SQL Server;
  el tenant se fija desde la identidad (variable de sesión establecida por la app tras
  autenticar), nunca desde el payload.
- **Cifrado:** en reposo (TDE / cifrado del servicio con CMK cuando la clasificación lo
  exige); columna o aplicación para datos ultra sensibles (PAN, credenciales); llaves en
  KMS/Key Vault, no en la base.
- **Enmascaramiento y minimización:** vistas o enmascaramiento dinámico para soporte y
  reporting; datos de producción anonimizados antes de usarse en ambientes inferiores.
- **Auditoría:** acceso a datos sensibles y cambios de privilegios (pgAudit, Oracle
  Unified Auditing, SQL Server Audit, logs de auditoría de servicios NoSQL), enviados a
  un destino protegido.
- **Retención y borrado:** políticas por clase de dato (habeas data, regulación); borrado
  real/anonimización que alcance réplicas, backups según política y proyecciones.
- **NoSQL:** autenticación habilitada (Redis `AUTH`/ACL, MongoDB sin acceso anónimo),
  sin exposición pública, IAM por tabla/acción en DynamoDB con condiciones
  (`dynamodb:LeadingKeys` para aislar por tenant cuando aplica).
