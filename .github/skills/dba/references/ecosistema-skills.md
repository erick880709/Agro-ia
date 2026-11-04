# Ecosistema de skills: contratos con `dba`

`dba` no diseña la arquitectura global, no implementa features y no aprueba merges. Su
valor es validar, con criterio de DBA, cada decisión de datos que las otras skills toman,
y devolver observaciones que puedan procesar sin reinterpretarlas.

## Tabla de contenido

1. Flujo completo
2. archi (TO-BE con datos)
3. builder
4. code-review
5. aegis
6. terragrunt-iac
7. Handoffs

## 1. Flujo completo

```
archi 09/10 (motor) ─► dba select ─► recomendación + DA propuesto
archi 16 / 16.xx / 16.xx.y / 17 ─► dba design-review ─► 16.00 + 16.00.1 (DB-NNN)
        ▲                                                  │
        └──── archi dispone cada DB-NNN ◄──────────────────┘  (25 no es apto con bloqueantes sin disponer)
builder (HU con persistencia) ─► dba advise ─► restricciones, índices, plan de migración
builder cierra ─► code-review ──escala──► dba gate ─► db-review.md + db-findings.json
terragrunt-iac (RDS, DynamoDB, Cosmos…) ─► dba review (parámetros, backup, HA)
aegis ◄──► dba  (roles/RLS/cifrado: dba diseña, aegis verifica explotabilidad)
```

## 2. archi (TO-BE con datos)

**Cuándo:** Caso A o C cuando el TO-BE crea, cambia o retira persistencia: selección de
motor en `09`/`10`/`10.1`, `16-Modelo-de-Datos.md`, cualquier `16.xx`, esquemas físicos
`16.xx.y`, servicios de datos en `17` (instancias, réplicas, backups, regiones) o una
migración de datos AS-IS → TO-BE (`23`/`24`). También en reapertura incremental cuando
cambia un `DATA-xxx`.

**Consume:** `02`–`06` (alcance, restricciones, `QA-xx` de rendimiento, disponibilidad,
consistencia), `09`/`10`/`10.1`, `14.00` (operaciones y volumen), `15` (flujos y
transacciones), `16`/`16.xx`/`16.xx.y`, `17`/`17.4` (despliegue y costos), `19.1` (SEC de
datos), `20`, AS-IS en Caso C.

**Valida, como mínimo:**
- Motor adecuado al patrón de acceso y a la consistencia exigida (CAP/PACELC), sin
  persistencia políglota injustificada (`guia-catalogo-bases-de-datos.md` de archi).
- Relacional: invariantes en restricciones, claves, tipos (dinero en `NUMERIC`/`NUMBER`,
  fechas con zona), normalización/desnormalización justificada, índices para cada
  operación de `14.00`, particionamiento y retención.
- NoSQL: tabla de patrones de acceso → clave/índice que la sirve, distribución de la
  clave de partición (hot partitions), tamaño de ítem/documento/partición, consistencia
  de lectura, TTL, estrategia de agregados y proyecciones.
- Transacciones e idempotencia de los flujos de `15`; outbox/CDC si hay eventos.
- RPO/RTO alcanzables con la configuración de `17` (PITR, réplicas, multi-AZ/región).
- Diccionario físico de `16.xx` coherente con `16.xx.y` (el validador de archi revisa
  la correspondencia estructural; `dba` revisa la calidad técnica del contenido).
- Plan de migración de datos y de esquema en Caso C, con validación de equivalencia.

**Entrega:**
- `16.00-Revision-Experta-Datos_<Proyecto>.md` (ver plantilla `db-review-template.md`,
  sección archi) y `16.00.1-Observaciones-Datos_<Proyecto>.json` (`dba-findings/1`).
- Cada observación `DB-NNN` enlaza el artefacto y el ID afectado (`DATA-xxx`, `CT-xx`,
  `API-xxx-OP-xxx`, `DA-xxx`, `QA-xx`) y propone el cambio; no edita `16.xx`.

**Disposición por archi (obligatoria):** cada `DB-NNN` termina en uno de estos estados,
registrados en `16.00.1` (campo `disposition`) y reflejados en el artefacto dueño:

| Disposición | Significa | Dónde queda |
|---|---|---|
| `incorporada` | El artefacto dueño ya refleja el cambio | `16.xx`/`16.xx.y`/`17`/`20` con referencia `DB-NNN` |
| `rechazada-justificada` | Razón técnica verificable para no aplicarla | Motivo en `16.00.1`; `dba` puede retirar o mantener |
| `riesgo-aceptado` | Se asume con autoridad, compensación y fecha | `21` con `DB-NNN` y owner |
| `diferida` | Se resolverá después; solo para `menor`/`nit` | `21` o backlog |
| `pendiente` | Sin decisión | Impide declarar apto `25` si es `bloqueante`/`mayor` |

`25` no puede ser apto con un `DB-NNN` `bloqueante` o `mayor` en `pendiente` o `diferida`.
El validador de archi lo comprueba si existe `16.00.1`.

Si `dba` no está disponible, archi registra en `16` "Revisión experta de datos: No
disponible — <motivo>" y aplica su propia guía; la ausencia no bloquea.

## 3. builder

**Antes (`advise`):** con la HU/spec, entrega restricciones e índices necesarios, forma
de la migración (y si requiere expand/contract), transacción e idempotencia, consultas
esperadas con su índice, y AC técnicos de datos ("la migración no bloquea escrituras más
de N s en una tabla de 50 M filas"; "la consulta de movimientos usa índice por
`(cuenta_id, fecha)`"). Builder conserva el ownership de la spec.

**Después (`gate`):** recomendado en rigor estándar con persistencia; obligatorio en
reforzado con datos persistentes, migraciones sobre tablas existentes, cambios de
concurrencia o de motor. Entrada: el mismo paquete que a code-review. Salida:
`docs/changes/<id>/db-review.md` + `db-findings.json`.

**Cierre:** builder no declara `completed` en reforzado con un `DB-NNN` `bloqueante` o
`mayor` abierto, ni con una migración marcada `no-concluyente` por falta de volumen o
destino de prueba que pueda volverla bloqueante.

## 4. code-review

- Escala a `dba` cuando el diff toca migraciones, DDL, mapeos ORM, repositorios/queries,
  configuración de datasource/pool, procedimientos o IaC de bases de datos y la pasada
  necesita criterio de DBA (bloqueos, planes, aislamiento, NoSQL).
- Misma escala: `bloqueante`, `mayor`, `menor`, `nit`, `pregunta`. code-review referencia
  el `DB-NNN` en vez de duplicar la tarjeta.
- Ninguna de las dos aprueba con un `DB-NNN` `bloqueante`/`mayor` abierto.

## 5. aegis

Frontera: `dba` diseña y revisa **controles de datos** (roles y privilegios, RLS,
cifrado en reposo/columna, enmascaramiento, auditoría, retención). `aegis` evalúa
**explotabilidad** (inyección SQL/NoSQL, IDOR, exposición de secretos, permisos IAM sobre
el servicio de datos). Si uno encuentra algo del otro, lo referencia y hace handoff.

## 6. terragrunt-iac

Para recursos de datos (RDS/Aurora, DynamoDB, DocumentDB, ElastiCache, Cosmos DB, Azure
SQL, Cloud SQL, Keyspaces, OpenSearch) revisa: versión de motor, clase/capacidad,
grupos de parámetros, backups/PITR y retención, multi-AZ/réplicas, cifrado con CMK,
`deletion_protection`/`prevent_destroy`, ventanas de mantenimiento, auto-scaling,
Performance Insights/monitoreo. Los hallazgos de exposición o IAM van a `aegis`.

## 7. Handoffs

```markdown
### Handoff → <skill>
- **Origen:** DB-004 (db-findings.json) / DATA-012
- **Motivo:** <una frase>
- **Insumo entregado:** <rutas>
- **Esperado de vuelta:** <disposición, artefacto o decisión>
- **Bloquea:** sí/no — <qué>
```
