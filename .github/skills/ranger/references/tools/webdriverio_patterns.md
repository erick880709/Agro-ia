# Suites WebdriverIO existentes

Ranger conserva esta guía porque no hay un especialista WebdriverIO en el kit. Para Selenium Java/pytest usa [qa-ranger-selenium](../../../qa-ranger-selenium/SKILL.md). Mantén el stack instalado; `ensure-qa-dependencies.mjs` no prepara WebdriverIO.

## Configuración y ejemplos

Para una suite WebdriverIO existente, lee su configuración, runner, plugins,
versiones y comandos. Respeta sus page objects y sus IDs de caso. Los siguientes
fragmentos ilustran el encargo; adapta la captura del runner al contrato.

```typescript
// wdio.conf.ts: fragmento para integrar en la configuración existente.
export const config: WebdriverIO.Config = {
  runner: 'local',
  specs: ['./e2e/**/*.spec.ts'],
  capabilities: [{ browserName: 'chrome' }],
  baseUrl: process.env.QA_BASE_URL,
  framework: 'mocha',
  reporters: ['spec', ['allure', { outputDir: 'resources/qa/wdio-results' }]],
};
```

```typescript
it('TC-01 [critical] - Login con credenciales válidas', async () => {
  await $('[aria-label="Email"]').setValue(process.env.QA_USER_EMAIL!);
  await $('[aria-label="Password"]').setValue(process.env.QA_USER_PASSWORD!);
  await $('button=Ingresar').click();
  await expect($('[data-testid="dashboard"]')).toBeDisplayed();
});
```

Configura hooks antes del cierre del navegador para guardar evidencia de éxito
y fallo. Un reporter Allure instalado no acredita que exista video o traza.
Verifica los archivos y su vínculo por caso, incluidos los intentos paralelos.


## Reportes y evidencia

Aplica la [guía común](../evidence_guide.md). Configura el reporter CTRF compatible con el runner instalado o convierte su reporte nativo; declara el CTRF como `test_results`. Allure por sí solo no acredita video, trace ni screenshot. Conserva IDs y prioridades y verifica los adjuntos reales antes del cierre.
