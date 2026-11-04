# Responsabilidades de automatización QA

Ranger selecciona el nivel y la herramienta, conserva el alcance del runbook y coordina el cierre. Consulta únicamente las guías de la herramienta elegida; la implementación vive en su especialista.

| Trabajo | Recurso canónico |
|---|---|
| Playwright: POM, fixtures, asincronía, pasos y escenarios avanzados | [Patrones Playwright](../../qa-ranger-playwright/references/14-patrones-automatizacion.md) |
| Playwright: grabación, video, trace y captura | [Evidencia Playwright](../../qa-ranger-playwright/references/13-evidencia-video.md) |
| Unitarias React/JavaScript: factories, Jest/RTL, MSW y snapshots | [Patrones unitarios](../../qa-ranger-unitarias/references/04-patrones-javascript.md) |
| Selenium Java/pytest: framework, localizadores y esperas | [Especialista Selenium](../../qa-ranger-selenium/SKILL.md) |
| Robot Framework: keywords, resources, BD, API y web | [Especialista Robot Framework](../../qa-ranger-robotframework/SKILL.md) |
| BDD: decisión y escenarios compartidos | [BDD/Gherkin](tools/bdd_gherkin_patterns.md) |
| Cypress existente | [Cypress](tools/cypress_patterns.md) |
| WebdriverIO existente | [WebdriverIO](tools/webdriverio_patterns.md) |
| Appium móvil | [Appium](tools/appium_mobile_patterns.md) |

Cypress, WebdriverIO y Appium conservan sus guías en Ranger porque no tienen una skill dedicada. Las [reglas de evidencia](evidence_guide.md), el contrato y el evaluador son comunes a todos los runners. Una guía de otra herramienta sirve como contexto, no autoriza migrar la suite.
