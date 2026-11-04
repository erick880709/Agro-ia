# 01 — Setup y configuración

## Contenido
1. Instalación
2. `playwright.config.ts` de referencia (comentado)
3. Proyectos: navegadores, dispositivos, setup, roles
4. Ambientes y variables
5. `webServer`
6. Timeouts
7. APIs por versión (1.55 → 1.63)

---

## 1. Instalación

```bash
npm init playwright@latest            # asistente: TS, carpeta tests, GitHub Actions, navegadores
# o en un proyecto existente:
npm i -D @playwright/test
npm i -D playwright-ctrf-json-reporter     # salida CTRF directa del runner
npx playwright install --with-deps chromium     # solo lo necesario; --with-deps instala libs del SO en Linux/CI
npx playwright --version
```
- Node 20+ (los LTS vigentes). Fija la versión exacta en `package.json` (`"@playwright/test": "1.63.0"`) y actualiza deliberadamente: cada versión trae navegadores nuevos y algunos cambios incompatibles.
- Detrás de proxy corporativo: `HTTPS_PROXY=...` para la descarga; o `PLAYWRIGHT_DOWNLOAD_HOST` apuntando a un mirror interno (Artifactory/Nexus).
- Navegadores de marca: `channel: 'chrome'` o `'msedge'` usa el navegador instalado en el sistema (útil cuando la política corporativa exige Edge).
- Desde 1.62 se incluyen `npx playwright mcp` y `npx playwright cli` (ver 10).

## 2. Config de referencia

```ts
// playwright.config.ts
import { defineConfig, devices } from '@playwright/test';
import { randomUUID } from 'node:crypto';
import 'dotenv/config';                         // npm i -D dotenv; .env NO se versiona

const isCI = !!process.env.CI;
// Playwright evalúa el config en cada worker: guardar el ID en process.env lo hereda a todos.
const runId = (process.env.QA_RUN_ID ||= randomUUID());
if (!/^[a-zA-Z0-9][a-zA-Z0-9._-]*$/.test(runId)) throw new Error('QA_RUN_ID inválido');
const resultsDir = `resources/qa/test-results/${runId}`;
const reportsDir = `resources/qa/reports/${runId}`;
const SLOWMO_MS = Number(process.env.QA_SLOWMO_MS ?? 300); // pausa entre acciones: video legible
const CTRF_REPORTER: [string, object] = ['./reporters/evidence-ctrf.ts', {
  runId, projectRoot: process.cwd(), outputDir: reportsDir, outputFile: 'ctrf.json', annotations: true,
}];

export default defineConfig({
  testDir: './tests',
  outputDir: resultsDir,
  fullyParallel: true,                          // paraleliza tests dentro de cada archivo
  forbidOnly: isCI,                             // falla el pipeline si alguien deja test.only
  retries: isCI ? 2 : 0,                        // en local, ver el fallo de inmediato
  retryStrategy: isCI ? 'isolated' : 'immediate', // 1.62+: reintentos al final, aislados
  workers: isCI ? 4 : undefined,
  timeout: 30_000 + SLOWMO_MS * 30,             // por test; escala con el slowMo
  expect: { timeout: 5_000 },                   // por aserción web-first
  reporter: isCI
    ? [CTRF_REPORTER, ['blob'], ['junit', { outputFile: `${reportsDir}/junit.xml` }], ['json', { outputFile: `${resultsDir}/results.json` }]]
    : [CTRF_REPORTER, ['list'], ['html', { open: 'never', outputFolder: `${reportsDir}/html` }], ['json', { outputFile: `${resultsDir}/results.json` }]],
  use: {
    baseURL: process.env.BASE_URL ?? 'http://localhost:3000',
    testIdAttribute: 'data-testid',             // cambiar si el equipo usa data-qa, data-cy, etc.
    trace: 'on',                               // Política QA: conservar cada caso
    screenshot: 'on',
    video: 'on',
    launchOptions: { slowMo: SLOWMO_MS },      // 0 en un gate puramente funcional; 600+ para demos
    actionTimeout: 10_000,
    navigationTimeout: 20_000,
    locale: 'es-CO',
    timezoneId: 'America/Bogota',               // determinismo en fechas
  },
  projects: [
    { name: 'setup', testMatch: /.*\.setup\.ts/ },
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'], storageState: 'playwright/.auth/user.json' },
      dependencies: ['setup'],
    },
    {
      name: 'firefox',
      use: { ...devices['Desktop Firefox'], storageState: 'playwright/.auth/user.json' },
      dependencies: ['setup'],
    },
    {
      name: 'mobile',
      use: { ...devices['Pixel 7'], storageState: 'playwright/.auth/user.json' },
      dependencies: ['setup'],
      grep: /@mobile/,
    },
  ],
});
```
Agrega `playwright/.auth/`, `resources/qa/test-results/`, `resources/qa/reports/`, `blob-report/` y `.env` al `.gitignore`.
Ignora también `resources/qa/*/*/*/attempt-*/`, donde se copian las evidencias por caso.

El scaffold incluye [reporters/evidence-ctrf.ts](../templates/project/reporters/evidence-ctrf.ts).
En proyectos existentes cópialo al proyecto y coloca su entrada primero en `reporter`.
Organiza los adjuntos por caso, runId, proyecto e intento y utiliza el paquete CTRF
instalado para generar el JSON. Las rutas del CTRF son relativas a la raíz del
proyecto; comparte `resources/qa/` conservando esa estructura.
`projectRoot` identifica esa raíz, aunque la configuración esté en una subcarpeta.
Ejecuta desde la raíz del proyecto o proporciona su ruta explícita en esta opción.

`npx playwright test` genera directamente `resources/qa/reports/<runId>/ctrf.json`,
tanto en local como en CI. No necesita un conversor ni scripts de Ranger. Conserva
ese archivo aunque existan pruebas fallidas: el reporte registra sus resultados,
mientras el código de salida del runner comunica el fallo de la corrida.

En proyectos existentes conserva los reporters que ya tengan y añade esta entrada primero.
`--reporter=...` reemplaza los reporters y sus opciones. Para conservar la
organización por caso, configura los reporters en el archivo y ejecuta sin ese flag.
Esta configuración corresponde a Playwright Test de Node; otros
bindings de Playwright usan sus propios runners.

## 3. Proyectos

Un proyecto = una combinación de configuración (navegador, dispositivo, rol, ambiente). Patrones:
- **setup → dependencias**: el proyecto `setup` autentica y los demás dependen de él (ver 04). Para limpiar al final: `teardown: 'cleanup'` en el setup.
- **Por rol**: `admin` y `cliente`, cada uno con su `storageState`.
- **Smoke vs regresión**: `grep: /@smoke/` en un proyecto liviano para cada despliegue.
- Ejecutar un proyecto: `npx playwright test --project=chromium`.

## 4. Ambientes

```ts
// config/env.ts — una sola fuente para URLs por ambiente
const ENVS = {
  dev: { baseURL: 'https://dev.app.ejemplo.com', apiURL: 'https://api-dev.ejemplo.com' },
  qa:  { baseURL: 'https://qa.app.ejemplo.com',  apiURL: 'https://api-qa.ejemplo.com' },
} as const;
export type EnvName = keyof typeof ENVS;
const name = (process.env.TEST_ENV ?? 'qa') as EnvName;
if (!ENVS[name]) throw new Error(`TEST_ENV no soportado: ${name}`);
export const env = { name, ...ENVS[name] };
```
Credenciales solo desde variables de entorno o el vault del pipeline. Valida al inicio que existan y falla con un mensaje claro si no.

## 5. `webServer`

Levanta la app antes de las pruebas (local o CI de la propia app):
```ts
webServer: {
  command: 'npm run start',
  url: 'http://localhost:3000/health',
  reuseExistingServer: !process.env.CI,
  timeout: 120_000,
  stdout: 'pipe',
  // wait: { stdout: /Listening on port (?<PORT>\d+)/ }   // 1.57+: esperar una línea de salida
},
```
Admite un arreglo para varios servicios (frontend + mock backend).

## 6. Timeouts

| Nivel | Default | Dónde |
|---|---|---|
| Test | 30 s | `timeout` / `test.setTimeout()` / `test.slow()` (×3) |
| Aserción web-first | 5 s | `expect.timeout` / `{ timeout }` en la aserción |
| Acción | sin límite propio (acotada por el test) | `use.actionTimeout` |
| Navegación | sin límite propio | `use.navigationTimeout` |
| Suite completa | sin límite | `globalTimeout` (útil en CI) |

Subir timeouts globales para "arreglar" flakiness oculta problemas: ver 08.

## 7. APIs por versión

Usa esta tabla para no introducir APIs que la versión del proyecto no tiene.

| Versión | Novedades relevantes para QA |
|---|---|
| 1.55 | `TestStepInfo.titlePath`; mejoras de codegen |
| 1.56 | **Test Agents** (`npx playwright init-agents`); `page.consoleMessages()`, `page.pageErrors()`, `page.requests()` |
| 1.57 | Chrome for Testing como Chromium; `webServer.wait` sobre stdout; `config.tag`; `locator.describe()` |
| 1.58 | Mejoras en la línea de tiempo de UI mode / trace viewer |
| 1.59 | Screencast (`page.screencast`); **debugger CLI para agentes** (`--debug=cli`); **Trace CLI** (`npx playwright trace`); trace `'retain-on-failure-and-retries'`; `await using` |
| 1.60 | HAR en tracing; `locator.drop()`; `toMatchAriaSnapshot` sobre `page`; **`test.abort()`**; opción `description` en `getByRole`. Elimina `videosPath`/`videoSize` (usar `recordVideo`) y `Locator.ariaRef()` |
| 1.61 | Passkeys WebAuthn (`context.credentials`); `page.localStorage`/`sessionStorage`; `expect.soft.poll()`; `-G` = `--grep-invert` |
| 1.62 | Component testing con stories/galleries; `AbortSignal` (`signal`) en acciones y aserciones; capturas WebP; **`retryStrategy: 'isolated'`**; `locator.waitForFunction()`; `apiResponse.timing()`; MCP y CLI incluidos (`npx playwright mcp` / `cli`); portapapeles aislado en headless |
| 1.63 | **Test locks** (`{ lock: 'nombre' }`); **`locator.visible()`** (reemplaza `:visible`); `frameLocator()` sin selector busca en todos los frames; `params`/`subtitle` en `test.step`; aria+screen snapshots en traces; `request.get<T>()` tipado; `--add-reporter`; reporter `perfetto`; `ariaSnapshotJSON()` |

Notas de compatibilidad: Ubuntu 20.04 sin soporte desde 1.63; Debian 11 desde 1.62; WebKit en macOS 14 retirado en 1.59; paquetes `@playwright/experimental-ct-*` sin actualizaciones desde 1.63 (migrar al modelo de stories).
