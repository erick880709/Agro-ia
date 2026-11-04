import { defineConfig, devices } from '@playwright/test';
import { randomUUID } from 'node:crypto';
import 'dotenv/config';
import { env } from './config/env';

const isCI = !!process.env.CI;
const STORAGE_STATE = 'playwright/.auth/user.json';
// El programa que encarga las pruebas puede proporcionar su runId.
// Si falta, genera otro identificador para separar las corridas.
// Playwright lee este archivo en el proceso principal y en los procesos de ejecución (workers).
// Guarda el ID en process.env para compartirlo con esos procesos y usar una carpeta por corrida.
const runId = (process.env.QA_RUN_ID ||= randomUUID());
if (!/^[a-zA-Z0-9][a-zA-Z0-9._-]*$/.test(runId)) {
  throw new Error('QA_RUN_ID debe ser un ID sin separadores de ruta');
}
const resultsDir = `resources/qa/test-results/${runId}`;
const reportsDir = `resources/qa/reports/${runId}`;
// La pausa entre acciones facilita la revisión del video.
const SLOWMO_MS = Number(process.env.QA_SLOWMO_MS ?? 300);
const CTRF_REPORTER: [string, object] = ['./reporters/evidence-ctrf.ts', { runId, projectRoot: process.cwd(), outputDir: reportsDir, outputFile: 'ctrf.json', annotations: true }];

export default defineConfig({
  testDir: './tests',
  outputDir: resultsDir,
  fullyParallel: true,
  forbidOnly: isCI,
  retries: isCI ? 2 : 0,
  retryStrategy: isCI ? 'isolated' : 'immediate',
  workers: isCI ? 4 : undefined,
  // Un caso con muchos pasos y slowMo alto puede superar el límite predeterminado de 30 s.
  timeout: 30_000 + SLOWMO_MS * 30,
  expect: { timeout: 5_000 },
  // CTRF (https://ctrf.io) es el resultado que leen el contrato QA y el reporte de ejecución:
  // casos, reintentos y evidencias salen de aquí, no de una transcripción.
  reporter: isCI
    ? [CTRF_REPORTER, ['blob'], ['junit', { outputFile: `${reportsDir}/junit.xml` }], ['json', { outputFile: `${resultsDir}/results.json` }]]
    : [CTRF_REPORTER, ['list'], ['html', { open: 'never', outputFolder: `${reportsDir}/html` }], ['json', { outputFile: `${resultsDir}/results.json` }]],
  use: {
    baseURL: env.baseURL,
    testIdAttribute: 'data-testid',
    // La política de navegador predeterminada conserva evidencia también de los casos exitosos.
    // Cambia esa política solo ante una excepción explícita o para pruebas API sin navegador.
    trace: 'on',
    screenshot: 'on',
    video: 'on',
    launchOptions: { slowMo: SLOWMO_MS },
    actionTimeout: 10_000,
    navigationTimeout: 20_000,
    locale: 'es-CO',
    timezoneId: 'America/Bogota',
  },
  projects: [
    { name: 'setup', testMatch: /.*\.setup\.ts/ },
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'], storageState: STORAGE_STATE },
      dependencies: ['setup'],
    },
{{EXTRA_PROJECTS}}  ],
{{WEB_SERVER}}});
