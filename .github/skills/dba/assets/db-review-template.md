---
db_review:
  id: <DBR-NNN | ID del cambio | 16.00>
  objetivo: change | architecture | repo
  revision: <sha | snapshot/hash de artefactos de archi>
  modo: design-review | review | gate | migrate | data-migration | tune | operate
  motores: [{motor: postgresql, version: "16", modalidad: aurora}]
  veredicto: aprobado | aprobado-con-observaciones | cambios-requeridos | no-concluyente
  conteos: {bloqueante: 0, mayor: 0, menor: 0, nit: 0, preguntas: 0}
  observaciones:
    - {id: DB-001, severidad: bloqueante, confianza: media, ubicacion: "ruta:línea | 16.03 §Diccionario", estado: abierto, disposicion: pendiente}
  findings_json: <ruta>/db-findings.json | 16.00.1-Observaciones-Datos_<Proyecto>.json
---

# Revisión experta de datos — <cambio o proyecto>

**Veredicto:** <una línea accionable>

## Resumen

<2–3 frases: qué se revisó, motores y la lectura del DBA.>

## Contexto y supuestos

| Dato | Valor | Fuente |
|---|---|---|
| Motor / versión / modalidad | | |
| Volumen de tablas/colecciones críticas | | 16.xx / consulta / supuesto |
| RPO / RTO | | 05 / 17 / línea base |
| Herramienta de migración y ORM | | |

## Herramientas ejecutadas

| Herramienta | Resultado | Nota |
|---|---|---|
| db_triage | | |
| migration_lint | | |
| EXPLAIN / pruebas | not_run | <motivo> |

## Cobertura por eje

| Eje | Estado | Nota |
|---|---|---|
| Modelo e integridad | ✅/⚠️/❌/— | |
| Consultas e índices | | |
| Transacciones y concurrencia | | |
| Evolución (migraciones) | | |
| Operación (backup, HA, capacidad) | | |
| Seguridad de datos | | |

## Observaciones

### DB-001 · <título>
- **Dónde:** `<archivo:línea>` · <DATA-xxx / CT-xx / API-xxx-OP-xxx>
- **Severidad / confianza:** <bloqueante / media>
- **Escenario:** <volumen, concurrencia, versión que lo dispara>
- **Evidencia:** <plan, lint, conteo, artefacto>
- **Remedio:** <DDL/código en el dialecto + plan de aplicación>
- **Verificación:** <cómo comprobar que quedó resuelto>
- **Decisión / disposición:** [ ] aceptar/incorporar [ ] rechazar con razón [ ] riesgo aceptado [ ] diferir (solo menor/nit)

## Preguntas

- **DB-00N:** <pregunta> — Consulta para resolverla: `<SQL/CLI de solo lectura>`

## Sección para archi (solo en `design-review`)

| DB | Severidad | Artefacto dueño | ID afectado | Cambio propuesto | Disposición archi | Nota |
|---|---|---|---|---|---|---|
| DB-001 | bloqueante | 16.03 | DATA-007 | `monto numeric(18,2)` | pendiente | |

`25` no puede declararse apto con un `bloqueante` o `mayor` en `pendiente` o `diferida`.

## Handoffs

- **builder:** <observaciones a corregir>
- **archi:** <decisiones o DA propuestos>
- **aegis:** <hallazgos de explotabilidad>
- **terragrunt-iac:** <parámetros, backups, HA en IaC>

## Rondas
