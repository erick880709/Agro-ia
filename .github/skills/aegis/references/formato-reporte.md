# Formato del reporte de seguridad

El JSON es el registro; el Markdown se renderiza desde él y nunca cambia un veredicto,
severidad o bloqueo. Compatible con code-review (bloque YAML, tarjetas, decisiones).

## Ubicación

1. Con expediente del cambio: `docs/changes/<id>/security-review.md` +
   `docs/changes/<id>/security-findings.json`. En re-revisión, misma ruta con `## Ronda N`.
2. Sin expediente: `docs/security/SR-NNN-<slug>.md` + `SR-NNN-<slug>.findings.json`
   (siguiente número disponible; slug kebab-case de 2–5 palabras).
3. Convención propia del proyecto si existe. Sin filesystem: en la respuesta.

## `security-findings.json`

```json
{
  "schema": "aegis-findings/1",
  "target": {"repo": "svc-cuentas", "base": "origin/main", "head": "a1b2c3d", "change_id": "PROJ-123"},
  "mode": "gate",
  "coverage": {
    "evaluated": ["A01","A05","A07","API1","API3","secrets","deps"],
    "not_applicable": [{"id": "LLM", "reason": "sin componentes de IA"}],
    "not_covered": [{"unit": "consumer-kafka", "reason": "fuera del diff"}],
    "tools": [{"name": "semgrep", "version": "1.x", "status": "run"}, {"name": "codeql", "status": "not_run"}]
  },
  "sec_requirements": [{"id": "SEC-004", "status": "ausente", "evidence": "Handler.java:42"}],
  "findings": [
    {
      "id": "HS-001",
      "fingerprint": "authz:movements-list:missing-owner-filter",
      "verdict": "confirmed",
      "title": "El listado de movimientos no verifica el titular de la cuenta",
      "cwe": "CWE-639",
      "owasp_category": "API1:2023",
      "location": {"file": "infrastructure/entry-points/reactive-web/src/main/java/co/x/Handler.java", "line": 42},
      "trace": [
        {"kind": "entrypoint", "file": "...RouterRest.java", "line": 18, "description": "GET /accounts/{id}/movements"},
        {"kind": "propagation", "file": "...Handler.java", "line": 42, "description": "id del path al use case sin principal"},
        {"kind": "sink", "file": "...MovementAdapter.java", "line": 30, "description": "findByAccountId(id)"}
      ],
      "evidence": [{"file": "...Handler.java", "line": 42, "description": "no usa ReactiveSecurityContextHolder"}],
      "counterevidence": "Se buscó filtro en SecurityWebFilterChain, use case y adapter: solo hay authenticated()",
      "confidence": "medium",
      "reproduced": false,
      "severity": {
        "likelihood": {"score": "high", "reason": "cualquier cliente autenticado cambia el id"},
        "impact": {"score": "high", "reason": "movimientos financieros de terceros (PII)"},
        "overall": "high"
      },
      "review_severity": "bloqueante",
      "sec_refs": ["SEC-004"],
      "remediation": "Pasar el titular del token al use case y filtrar en el gateway (findByIdAndOwner)",
      "negative_test": "Dado JWT del cliente A, cuando GET /accounts/{cuentaDeB}/movements, entonces 403 y sin consulta al adapter",
      "status": "abierto"
    }
  ],
  "hardening_notes": ["Cabecera Referrer-Policy ausente en el BFF"],
  "verdict": "cambios-requeridos"
}
```

Reglas que valida `scripts/validate_findings.py`:
- `fingerprint` estable de causa raíz: sin números de línea, severidad ni veredicto.
- `confirmed`: traza ≥ 2 pasos que empieza en `entrypoint` y termina en `sink`, ≥ 1
  evidencia, `severity` con `overall ≤ impact`, `review_severity` coherente con el mapeo,
  `confidence: high` solo con `reproduced: true`.
- `needs_validation`: `blockers` no vacío y `validation_plan`; sin `severity`.
- `rejected`: `ruled_out_by {control, location}`; sin `severity`.
- `counterevidence` en todos.
- Ningún campo contiene un secreto sin enmascarar (heurística por prefijos).
- `verdict` global coherente con los hallazgos y la cobertura.

Estados de seguimiento: `abierto`, `aceptado`, `rechazado`, `diferido`, `riesgo-aceptado`
(exige autoridad, motivo, compensación y fecha de revisión), `corregido`, `verificado`,
`reabierto`.

## Markdown

Usa [la plantilla](../assets/security-report-template.md):
1. Bloque YAML `security_review:` (id, cambio, revisión, modo, veredicto, conteos,
   hallazgos `{id, review_severity, confidence, file, status}`).
2. Veredicto en una línea accionable.
3. Resumen (2–3 frases) y superficie analizada.
4. Cobertura (evaluado / no aplica / no cubierto / herramientas).
5. Verificación de `SEC-xxx` de archi (si aplica).
6. Hallazgos confirmados como tarjetas, por severidad.
7. Necesitan validación (con bloqueo y plan).
8. Notas de hardening (no cuentan).
9. Rechazados (no re-levantar) con el control que los descarta.
10. Handoffs (archi, builder, Vulcano, QA).
11. Rondas.

SARIF: `python scripts/to_sarif.py security-findings.json -o security.sarif` (solo
`confirmed`; añade `--include-needs-validation` si se quiere verlos en code scanning).
