# 12 — Reportes, evidencia y CTRF

## 1. Archivos de una corrida

```
resources/qa/
├── test-results/<runId>/
│   ├── output.xml, log.html, report.html, xunit.xml      # reporte nativo (no se borra)
│   ├── rerun1.xml …                                        # intentos adicionales
│   └── <CASE-ID>/attempt-<n>/video.webm|trace.zip|screenshot.png
└── reports/<runId>/
    ├── ctrf.json                                           # test_results del contrato
    ├── rtm.md                                              # trazabilidad
    └── execution-report.md                                 # generador común de Ranger
```

`QaEvidencia` crea la carpeta del caso a partir del ID del nombre o del tag; un test sin ID falla al pedir su carpeta (sin ID no hay trazabilidad de evidencia).

## 2. Evidencia por nivel

| Nivel | Política | Robot Framework |
|---|---|---|
| Base de datos / API | `api` → `raw_results` | `output.xml` + CTRF; sin adjuntos por caso |
| Web con Browser | `browser` → video, trace, screenshot por caso, también exitosos | plantilla `web-browser` |
| Web con SeleniumLibrary | `browser` | screenshot + traza diagnóstica; video solo con infraestructura que grabe |

Reducir tipos exige `override.reason` explícito del encargo. No declares adjuntos que no existen.

## 3. CTRF

```bash
python tools/ctrf_from_robot.py --output $OUT/output.xml [--output $OUT/rerun1.xml] \
    --out resources/qa/reports/$QA_RUN_ID/ctrf.json --evidencia $OUT [--proyecto chromium] --project-root .
```

- Identidad: prefijo del nombre o tag (`TC-`, `SEC-`, `FRAUD-`, `API-`, `A11Y-`, `UT-`, `PERF-`); prioridad: `[critical]` en el nombre o tag `critical`. Si vienen solo de tags, el nombre CTRF se compone como `ID [prioridad] nombre`.
- Casos sin ID o prioridad se avisan por stderr y el validador común los cuenta como error: corrige los nombres, no el CTRF.
- `--proyecto` solo para navegador. Estados: PASS→passed, FAIL→failed, SKIP→skipped, NOT RUN→other.
- Último intento con adjuntos `video|trace|screenshot`; previos como `attempt-<n>/<tipo>`; `retries` y `flaky` del historial.

Después: `node .claude/contracts/output/generate-execution-report.mjs --ctrf … --expected <casos.json> --exit-criteria <criterios.json> --out …/execution-report.md` y publica el veredicto calculado. Para enlazar evidencia de otra fuente, `../ranger/scripts/attach-evidence.mjs` usa la misma convención `<CASE-ID>/`.

## 4. Trazabilidad

`python tools/rtm_from_robot.py $OUT/output.xml --out resources/qa/reports/$QA_RUN_ID/rtm.md [--csv rtm.csv]` reconoce `[HU-123][CA-2]` en el nombre o tags `HU-123`, `CA-2` (también `RF-`, `REQ-`, `US-`, `AC-`).

## 5. Publicación en CI

- GitHub: `actions/upload-artifact` de `resources/qa/` con `if: always()`.
- Azure YAML: `PublishTestResults@2` (JUnit desde `xunit.xml`) + `PublishPipelineArtifact@1`.
- Release clásico: Publish Report (HTML) y la carpeta de resultados indicada en AutomationUse (08).
