# 09 — CI/CD y reportes

## Contenido
1. Principios
2. GitHub Actions con sharding y merge de reportes
3. Azure DevOps
4. Docker y Jenkins
5. Reporters
6. Trazabilidad requisito → prueba
7. Seguridad de artefactos

---

## 1. Principios

- `npm ci` (lockfile) + versión exacta de `@playwright/test` + `npx playwright install --with-deps <navegadores>` (solo los que se usan).
- Instala la misma versión de navegadores que la de la librería: la imagen Docker `mcr.microsoft.com/playwright:v<versión>-noble` ya los trae.
- Política: `@smoke` bloqueante en cada despliegue, regresión completa nocturna, visual/a11y como jobs separados.
- Conservar video, trace y screenshot de cada caso de navegador, incluidos los exitosos; no reducir la evidencia por estar en CI. Adaptar solo a una excepción explícita del encargo.
- Publicar siempre los artefactos (`if: always()` / `condition: always()`), incluso si las pruebas fallan.
- Fija acciones e imágenes por SHA/digest en pipelines sensibles.

## 2. GitHub Actions

```yaml
name: e2e
on:
  pull_request:
  workflow_dispatch:
    inputs:
      ambiente: { type: choice, options: [dev, qa, stg], default: qa }
jobs:
  test:
    runs-on: ubuntu-latest
    timeout-minutes: 30
    strategy:
      fail-fast: false
      matrix:
        shard: [1/4, 2/4, 3/4, 4/4]
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with: { node-version: 22, cache: npm }
      - run: npm ci
      - run: npx playwright install --with-deps chromium
      - run: npx playwright test --shard=${{ matrix.shard }}
        env:
          CI: 'true'
          QA_RUN_ID: github-${{ github.run_id }}-${{ github.run_attempt }}-${{ strategy.job-index }}
          TEST_ENV: ${{ inputs.ambiente || 'qa' }}
          E2E_USER: ${{ secrets.E2E_USER }}
          E2E_PASSWORD: ${{ secrets.E2E_PASSWORD }}
      - uses: actions/upload-artifact@v4
        if: ${{ !cancelled() }}
        with:
          name: blob-report-${{ strategy.job-index }}
          path: blob-report
          retention-days: 7
      - uses: actions/upload-artifact@v4
        if: ${{ !cancelled() }}
        with:
          name: qa-evidence-${{ strategy.job-index }}
          path: resources/qa
          retention-days: 14

  report:
    if: ${{ !cancelled() }}
    needs: test
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with: { node-version: 22, cache: npm }
      - run: npm ci
      - uses: actions/download-artifact@v4
        with: { path: all-blob-reports, pattern: blob-report-*, merge-multiple: true }
      - run: npx playwright merge-reports --config reporters/merge.config.ts ./all-blob-reports
        env:
          QA_RUN_ID: github-${{ github.run_id }}-${{ github.run_attempt }}-merged
      # Freno de la corrida: falla el job si el veredicto agregado es NO-GO. Requiere el kit en .claude/;
      # agrega --expected <casos.json> para que el alcance acordado cuente en el veredicto.
      - run: node .claude/contracts/output/generate-execution-report.mjs --ctrf resources/qa/reports/github-${{ github.run_id }}-${{ github.run_attempt }}-merged/ctrf.json --out resources/qa/reports/github-${{ github.run_id }}-${{ github.run_attempt }}-merged/execution-report.md --fail-on-no-go
      - uses: actions/upload-artifact@v4
        if: ${{ !cancelled() }}
        with: { name: qa-report-merged, path: resources/qa, retention-days: 14, if-no-files-found: error }
```
Con sharding, el reporter de cada shard debe ser `blob`; el HTML final se arma con `merge-reports`. En PRs, el reporter `github` anota los fallos en el diff.
Conserva también el reporter organizador primero en cada shard. El scaffold incluye
`reporters/merge.config.ts`: reconstruye las carpetas por caso, navegador e intento
y genera el CTRF consolidado con evidencia de reintentos y adjuntos en memoria,
además del HTML y el `junit.xml` unidos, todo en `resources/qa/reports/<runId>/`.
El artefacto se sube sin el prefijo `resources/qa/`. Para que los enlaces del CTRF
resuelvan, descomprímelo en `resources/qa/` de la raíz del proyecto (por ejemplo,
`actions/download-artifact` con `path: resources/qa`).

## 3. Azure DevOps

```yaml
trigger: none
parameters:
  - name: ambiente
    type: string
    default: qa
    values: [dev, qa, stg]
  - name: grep
    type: string
    default: '@smoke'

pool: { vmImage: ubuntu-latest }
variables:
  - group: e2e-secrets-${{ parameters.ambiente }}     # E2E_USER, E2E_PASSWORD (secretas)
  - name: CI
    value: 'true'

jobs:
  - job: e2e
    strategy:
      parallel: 3                                     # sharding nativo de Azure
    timeoutInMinutes: 45
    steps:
      - task: NodeTool@0
        inputs: { versionSpec: '22.x' }
      - script: npm ci
        displayName: Instalar dependencias
      - script: npx playwright install --with-deps chromium
        displayName: Instalar navegadores
      - script: npx playwright test --grep "${{ parameters.grep }}" --shard=$(System.JobPositionInPhase)/$(System.TotalJobsInPhase)
        displayName: Playwright ${{ parameters.ambiente }}
        env:
          QA_RUN_ID: azure-$(Build.BuildId)-$(System.JobPositionInPhase)
          TEST_ENV: ${{ parameters.ambiente }}
          E2E_USER: $(E2E_USER)                       # las secretas de Azure se mapean explícitamente
          E2E_PASSWORD: $(E2E_PASSWORD)
      - task: PublishTestResults@2
        condition: always()
        inputs:
          testResultsFormat: JUnit
          testResultsFiles: resources/qa/reports/**/junit.xml
          testRunTitle: Playwright ${{ parameters.ambiente }} $(System.JobPositionInPhase)
      - publish: resources/qa
        artifact: playwright-report-$(System.JobPositionInPhase)
        condition: always()
```
Si se necesita un único HTML consolidado, replica el patrón blob + job de merge del §2. Con agentes self-hosted en la red corporativa, preinstala navegadores en la imagen del agente o usa el contenedor oficial (`container: mcr.microsoft.com/playwright:v1.63.0-noble`).

## 4. Docker y Jenkins

```bash
docker run --rm --ipc=host -v "$PWD":/work -w /work \
  -e TEST_ENV=qa -e E2E_USER -e E2E_PASSWORD \
  mcr.microsoft.com/playwright:v1.63.0-noble \
  bash -c "npm ci && npx playwright test"
```
`--ipc=host` evita caídas de Chromium por memoria compartida. Jenkins: agente con esa imagen, `npx playwright test`, `junit 'resources/qa/reports/**/junit.xml'`; conserva también `resources/qa/test-results/` y genera HTML con merge de blobs.

## 5. Reporters

| Reporter | Para |
|---|---|
| `list` / `line` / `dot` | Consola local / CI compacto |
| `html` | Revisión humana: trace, capturas, video, pasos (`open: 'never'` en CI) |
| `junit` | Pestaña Tests de Azure/Jenkins/GitLab |
| `json` | Métricas, trazabilidad (`scripts/rtm_from_report.py`), dashboards |
| `blob` | Sharding + `merge-reports` |
| `github` | Anotaciones en PRs |
| `perfetto` (1.63+) | Línea de tiempo por worker para optimizar duración |
| Allure / ReportPortal / TestDino | Historial y tendencias (paquetes de terceros) |

`--add-reporter` (1.63+) agrega un reporter desde la CLI sin reemplazar los de la config. `testInfo.attach()` adjunta evidencia (JSON, capturas, logs) al reporte.

## 6. Trazabilidad

Vincula cada test a su requisito con:
- el título: `test('[HU-245][CA-1] transfiere con saldo suficiente', ...)`, o
- una anotación: `{ annotation: { type: 'req', description: 'HU-245/CA-1' } }`, o
- un tag: `{ tag: '@req:HU-245' }`.

Genera la matriz desde el reporte JSON:
```bash
npx playwright test    # el reporter JSON escribe por runId bajo resources/qa/test-results/
python scripts/rtm_from_report.py resources/qa/test-results/<runId>/results.json --out resources/qa/reports/<runId>/rtm.md --csv resources/qa/reports/<runId>/rtm.csv
```
Produce requisito → criterio → tests → estado (pasa, falla, flaky, omitido) y lista los tests sin trazabilidad.

## 7. Seguridad de artefactos

Traces, videos y reportes contienen pantallas con datos, cookies y requests: retención corta, acceso restringido y enmascaramiento (`mask` en capturas). No publicar reportes en páginas públicas desde repositorios de clientes. El directorio `playwright/.auth` nunca va como artefacto.
