# dba — experto en bases de datos del ecosistema de skills

DBA y arquitecto de datos para motores relacionales (PostgreSQL, Oracle, SQL Server,
MySQL/MariaDB y sus versiones administradas) y no relacionales (DynamoDB, MongoDB/
DocumentDB/Cosmos DB, Cassandra/ScyllaDB/Keyspaces, Redis, OpenSearch, grafos, series de
tiempo, vectores). Valida las decisiones de datos de **archi**, **builder** y
**code-review**, y se coordina con **aegis** y **terragrunt-iac**.

## Modos

`design` · `select` · `design-review` (archi) · `advise` y `gate` (builder) · `review`
(code-review) · `migrate` · `data-migration` · `tune` · `operate` · `procedure`.

## Estructura

```
dba/
├── SKILL.md
├── agents/openai.yaml
├── references/
│   ├── ecosistema-skills.md        # contratos con archi (16.00), builder, code-review, aegis, terragrunt-iac
│   ├── revision-y-severidad.md     # escala, verificación, db-findings.json, tarjetas
│   ├── modelado-relacional.md · modelado-nosql.md · seleccion-de-motor.md
│   ├── consultas-e-indices.md · transacciones-y-concurrencia.md
│   ├── migraciones-esquema.md · migracion-de-datos.md
│   ├── operacion-ha-dr.md · seguridad-datos.md · procedimientos-almacenados.md
│   ├── stacks-aplicacion.md        # Spring/JPA/R2DBC, Scaffold (jpa, r2dbc, mongodb, dynamodb, redis), Go
│   ├── evaluacion-conductual.md
│   └── motores/ postgresql · oracle · sqlserver · mysql · dynamodb · mongodb · cassandra-scylla · redis-busqueda-otros
├── scripts/
│   ├── db_triage.py                # motores, herramientas de migración, señales, plan (credenciales enmascaradas)
│   ├── migration_lint.py           # DDL riesgoso por motor; --base detecta migraciones aplicadas editadas; --new-database
│   └── validate_findings.py        # contrato dba-findings/1; --archi exige disposición
├── assets/ db-review-template.md · Linea_Base_Datos_template.md · plan-migracion-template.md
├── evals/evals.json
└── tests/test_dba_scripts.py
```

## Uso rápido

```bash
python scripts/db_triage.py <repo> --base origin/main --json /tmp/db-triage.json
python scripts/migration_lint.py src/main/resources/db/migration --engine postgresql --base origin/main
python scripts/validate_findings.py docs/changes/PROJ-1/db-findings.json
python -m unittest discover -s tests -v
```

## Integración aplicada en las otras skills

- **archi:** artefacto `16.00-Revision-Experta-Datos` + `16.00.1-Observaciones-Datos`;
  revisión antes de `CP-03` cuando el TO-BE define datos; `data-migration` en Caso C;
  disposición obligatoria de cada `DB-NNN`; el validador impide `25` apto con
  bloqueantes/mayores pendientes (`guia-catalogo-bases-de-datos.md` §8).
- **builder:** `advise` antes de implementar persistencia (paso 3) y `gate` al cerrar
  (paso 5); no cierra `completed` con `DB-NNN` bloqueante/mayor abierto.
- **code-review:** pasada H "Datos y persistencia" (`references/database.md`) con
  escalamiento a `dba` y mínimo propio si `dba` no está.
- **aegis:** frontera explícita (dba diseña controles de datos; aegis evalúa explotabilidad).

## Fuentes

u1pns/skill-dba, SimonBarnett/skill-dba (SQL Server: backups, salud, deadlocks),
antonrisch/db-skills (migraciones seguras, consultas lentas, calidad de datos),
microsoft/postgres-skills, neondatabase/postgres-skills, xiongcccc/pg-mastery,
scylladb/agent-skills, VoltAgent (database-administrator), claude-dev-suite (PostgreSQL),
0xfurai (dynamodb-expert), tons-of-skills (stored procedures), aws-samples/sample-dbmig-aidlc
(migración Oracle/SQL Server → PostgreSQL/MySQL), ECC, navigator, TerminalSkills,
OneWave, aj-geddes, rei-skills y Agent-Skills-4-Vibe-Coding (migraciones).
`DynamoDS/skills`, `ai-dynamo` y la documentación de NVIDIA Dynamo no tratan de
DynamoDB y no se usaron.
