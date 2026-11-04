import { defineConfig } from '@playwright/test';
import path from 'node:path';
import { randomUUID } from 'node:crypto';

const runId = process.env.QA_RUN_ID ?? `merged-${randomUUID()}`;
// Playwright resuelve las rutas de los reporters desde la carpeta de este archivo.
// Se fijan desde la raíz del proyecto para que el workflow publique todo bajo resources/qa/.
const reportsDir = path.join(process.cwd(), 'resources/qa/reports', runId);
export default defineConfig({
  reporter: [
    [path.join(__dirname, 'evidence-ctrf.ts'), { runId, projectRoot: process.cwd(), outputDir: reportsDir, outputFile: 'ctrf.json', annotations: true }],
    ['html', { open: 'never', outputFolder: path.join(reportsDir, 'html') }],
    ['junit', { outputFile: path.join(reportsDir, 'junit.xml') }],
  ],
});
