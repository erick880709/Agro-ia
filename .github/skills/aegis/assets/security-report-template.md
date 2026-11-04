---
security_review:
  id: SR-NNN            # o el ID del cambio (PROJ-123)
  cambio: <id/expediente o PR>
  revision: <sha | sin-commit + hash>
  base: <rama/sha>
  modo: audit | gate | iac | pipeline | supply-chain | agentic | container | re-review
  independencia: independiente | auto-revision
  veredicto: seguro | seguro-con-observaciones | cambios-requeridos | no-concluyente
  conteos: {bloqueante: 0, mayor: 0, menor: 0, preguntas: 0, hardening: 0, rechazados: 0}
  hallazgos:
    - {id: HS-001, review_severity: bloqueante, confidence: medium, file: "ruta:línea", status: abierto}
  findings_json: <ruta>/security-findings.json
---

# Revisión de seguridad — <título del cambio>

**Veredicto:** <una línea accionable, p. ej. "cambios requeridos: HS-001 permite leer movimientos de otro cliente">

## Resumen

<2–3 frases: qué cambió, superficie expuesta y lectura del revisor.>

## Superficie analizada

| Entrada | Principal | Activo | Frontera |
|---|---|---|---|
| `GET /accounts/{id}/movements` | Cliente autenticado | Movimientos (PII financiera) | Cliente ↔ datos de otro cliente |

## Cobertura

- **Evaluado:** <A01, A05, API1, secretos, dependencias…>
- **No aplica:** <categoría — motivo>
- **No cubierto:** <unidad — motivo> (impide `seguro`)
- **Herramientas:** <semgrep 1.x run | codeql not_run | …>
- **Excluidos por regla fija:** <n por regla>

## Requisitos de seguridad de arquitectura (19.1)

| SEC | Alcance | Estado en código | Evidencia |
|---|---|---|---|
| SEC-004 | CT-02 / API-003-OP-002 | ausente | `Handler.java:42` |

## Hallazgos confirmados

### HS-001 · <título específico>

- **Dónde:** `ruta/archivo:línea`
- **Severidad:** high (probabilidad high: <razón>; impacto high: <razón>) → **bloqueante** · confianza medium
- **Clasificación:** CWE-639 · API1:2023 · SEC-004
- **Frontera + resultado:** <principal> controla <entrada> y cruza <frontera>; el control <x> no se aplica; resultado: <concreto>.
- **Traza:** entrada `RouterRest.java:18` → `Handler.java:42` → sumidero `MovementAdapter.java:30`
- **Contraevidencia buscada:** <dónde se buscó la defensa y qué se encontró>
- **Remedio:** <cambio concreto en el idioma del stack, respetando la arquitectura>
- **Test negativo:** Dado <…>, cuando <…>, entonces <…>
- **Decisión:**
  - [ ] aceptar
  - [ ] rechazar (razón técnica)
  - [ ] diferir
  - [ ] riesgo aceptado (autoridad, compensación, fecha de revisión)

## Necesitan validación

### HS-00N · <título>
- **Bloqueo:** <hecho fuera del código>
- **Plan de validación:** <comando o consulta que el owner puede ejecutar>

## Notas de hardening (no cuentan para el veredicto)

- <nota>

## Rechazados (no re-levantar)

| ID | Candidato | Control que lo descarta | Ubicación |
|---|---|---|---|

## Handoffs

- **builder:** <hallazgos a corregir como bugfix>
- **archi:** <THR-propuesta / contradicción con 19.1>
- **Vulcano:** <control automatizable y evidencia esperada>
- **QA (ranger):** <casos negativos a automatizar>

## Rondas
