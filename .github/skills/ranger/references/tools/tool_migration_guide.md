# Guía de Migración entre Herramientas de Automatización

Cómo migrar una suite existente de una herramienta a otra sin perder
trazabilidad ni cobertura. Aplica el mismo principio en cualquier
dirección (Selenium→Playwright, Cypress→Playwright, Playwright→Cypress,
etc.) — las secciones específicas cubren las rutas más comunes.

---

## Índice

- [Principios Generales](#principios-generales)
- [Selenium → Playwright](#selenium--playwright)
- [Cypress → Playwright](#cypress--playwright)
- [Preservar Trazabilidad de Casos](#preservar-trazabilidad-de-casos)
- [Cuándo NO Migrar](#cuándo-no-migrar)

---

## Principios Generales

1. **Migrar incrementalmente por módulo/feature**, nunca todo de una vez.
   Un big-bang de migración bloquea al equipo de QA con dos suites rotas
   en paralelo y sin cobertura confiable durante la transición.
2. **Correr ambas suites en paralelo** durante el período de migración —
   la suite vieja sigue siendo la fuente de verdad hasta que la nueva
   cubre el mismo alcance y se validó que detecta los mismos defectos.
3. **Preservar los ids de caso** (`TC-xxx`, `SEC-xxx`, etc.) exactamente
   igual en la suite nueva — ver la sección de trazabilidad abajo. Esto es
   lo único no negociable del proceso.
4. **No es un ejercicio de traducción 1:1 automática** — es una
   oportunidad para corregir anti-patrones de la suite vieja (selectors
   frágiles, sleeps duros, estado compartido entre tests) en vez de
   copiarlos tal cual al nuevo framework.
5. **Definir un criterio de "listo para apagar la suite vieja"** antes de
   empezar: cobertura equivalente confirmada, N ejecuciones verdes
   consecutivas de la suite nueva en CI, sin regresiones detectadas que la
   vieja sí detectaba.

## Selenium → Playwright

Motivadores típicos: auto-wait nativo (elimina la mayoría de los waits
explícitos manuales), soporte multi-navegador real sin Grid, evidencia
integrada (video/trace) sin configurar Allure aparte, ejecución más rápida.

| Selenium (Java) | Playwright equivalente |
|---|---|
| `driver.findElement(By.cssSelector(...))` | `page.locator(...)` / `page.getByRole(...)` |
| `WebDriverWait` + `ExpectedConditions` | Aserciones web-first automáticas (`expect(locator).toBeVisible()`) |
| `ThreadLocal<WebDriver>` para paralelismo | Workers nativos de `@playwright/test`, sin manejo manual |
| Selenium Grid/Docker | `npx playwright test --workers=N`, o Grid propio si ya existe infraestructura |
| Allure con screenshot manual en fallo | Video/trace/screenshot automáticos por config |
| Page Object Model en Java | Page Object Model en TypeScript, misma estructura conceptual |

Pasos concretos:

1. Empezar por los casos `critical`/`high` de un módulo acotado — no por
   los más fáciles de portar, sino por los de mayor riesgo, para validar
   rápido que la suite nueva detecta lo mismo que la vieja.
2. Portar el Page Object correspondiente primero, con los mismos nombres
   de método cuando tenga sentido — reduce la carga cognitiva del equipo
   durante la transición.
3. Reemplazar cada `WebDriverWait` explícito por la aserción web-first
   equivalente — no portarlo como un `page.waitForTimeout()` "por
   velocidad", eso reintroduce el problema que Playwright resuelve nativamente.
4. Mantener el mismo id de caso en el título del test nuevo.
5. Correr ambas suites contra el mismo build y comparar resultados caso
   por caso antes de dar por migrado ese módulo.

## Cypress → Playwright

Motivadores típicos: necesidad de multi-pestaña/multi-contexto real,
soporte WebKit, trace portable para debug en CI headless.

| Cypress | Playwright equivalente |
|---|---|
| `cy.get()` / `cy.findByRole()` | `page.locator()` / `page.getByRole()` |
| Reintento automático de comandos/aserciones | Aserciones web-first automáticas (comportamiento similar) |
| `cy.intercept()` | `page.route()` / fixture `request` |
| `cy.session()` | `storageState` reutilizado entre tests |
| Video por archivo de spec | Video por test individual (más granular) |
| Sin trace portable | `trace.zip` con timeline completo |

Pasos concretos:

1. La migración suele ser más mecánica que Selenium→Playwright porque
   ambos tienen auto-wait — el riesgo principal es sintaxis, no arquitectura.
2. Revisar cualquier uso de `cy.origin()` (cross-origin) — en Playwright
   esto es nativo sin necesidad de un wrapper especial.
3. Los comandos custom (`Cypress.Commands.add`) se portan a fixtures o
   funciones helper de Playwright, no hay equivalente 1:1 directo.
4. Mantener el mismo id de caso en el título del test nuevo.

## Preservar Trazabilidad de Casos

El id de caso (`TC-xxx`/`SEC-xxx`/`FRAUD-xxx`/`API-xxx`/`A11Y-xxx`) es el
contrato que conecta el runbook, la evidencia histórica y los reportes de
ejecución (ver `../markdown_test_runbook.md`). Al migrar:

- El caso `TC-01` en la suite nueva debe seguir siendo `TC-01` — nunca
  renumerar durante una migración, aunque el orden lógico cambie.
- La evidencia histórica de la suite vieja (`resources/qa/TC-01/<runId
  viejo>/`) no se borra ni se mezcla con la de la suite nueva — ambas
  conviven bajo el mismo `CASE-ID`, con `runId`s distintos que ya
  distinguen de qué ejecución (y, si hace falta aclararlo, de qué
  herramienta) viene cada una.
- Si un caso de la suite vieja ya no aplica (funcionalidad eliminada, no
  solo migrada), documentarlo explícitamente como retirado en vez de
  dejarlo desaparecer en silencio — un id de caso que deja de aparecer sin
  explicación es indistinguible de un hueco de cobertura accidental.

## Cuándo NO Migrar

- El equipo no tiene bandwidth para mantener dos suites en paralelo
  durante la transición — mejor esperar a un momento con más margen que
  forzar una migración a medias.
- La motivación es solo "la herramienta nueva está de moda" sin un
  problema concreto que resolver — el costo de migración (tiempo,
  riesgo de introducir huecos de cobertura) rara vez se justifica sin una
  limitación real de la herramienta actual.
- La suite actual funciona bien y el problema real es otro (flaky por
  mal diseño de tests, falta de datos de prueba estables) — migrar de
  herramienta no arregla problemas de arquitectura de tests; ver
  `../qa_best_practices.md` primero.
