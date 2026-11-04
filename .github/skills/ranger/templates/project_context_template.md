# Plantilla de Contexto del Proyecto (`resources/qa/project-context.md`)

Instanciar este archivo en `resources/qa/project-context.md` la primera
vez que se aplica este skill sobre un proyecto (Paso 0.4 de `../SKILL.md`),
y releerlo al principio de cada conversación siguiente sobre el mismo
proyecto en vez de repetir el descubrimiento completo de los Pasos 0–0.1
desde cero. Actualizar solo las secciones que cambiaron, no reescribir
todo el archivo en cada uso.

## Encabezado Obligatorio

```markdown
# Contexto de QA del Proyecto

- Última actualización: <YYYY-MM-DD>
- Actualizado por: Claude Code (skill Ranger)
```

## 0. Tablero de Trabajo

- Tablero: `ninguno` | `Azure DevOps` | `Jira` (respuesta a la pregunta inicial; si es `ninguno`
  no se vuelve a preguntar).
- Organización/sitio y proyecto (p. ej. `personalsoftsas` / `<Proyecto>`, o `https://<sitio>.atlassian.net` / `<CLAVE>`).
- Servidor MCP configurado (nombre en `.mcp.json`) y método de autenticación — **nunca el token**.
- Actualización al terminar: `automático` | `mostrarme antes` | `no`.
- Mapeo de estados acordado: GO → `<estado>`, NO-GO → `<estado>`, incompleto → sin cambio.
- Work items del alcance actual (IDs).

## 1. Stack

- Framework y versión (`react`, `next`, u otro) — de `package.json`.
- Router de Next.js si aplica: `App Router` (`app/`) o `Pages Router`
  (`pages/`).
- Gestor de paquetes real (por lockfile): `npm`/`yarn`/`pnpm`/`bun`.
- Test runner unitario ya instalado (`jest`, `vitest`, ninguno).

## 2. Herramienta de Automatización

- Herramienta detectada o elegida (Paso 0.1): `Playwright` / `Cypress` /
  `Selenium (Java)` / `Selenium (WebdriverIO)` / `Appium` / más de una en
  convivencia.
- Si hay más de una: cuál es la vigente/recomendada y cuál está en proceso
  de retirarse (ver `../references/tools/tool_migration_guide.md` si aplica).
- Si el proyecto no tenía ninguna al momento de aplicar el skill, y se usó
  el default: nota de que fue una decisión de Ranger, no una preferencia
  explícita del equipo — puede revisarse si el equipo ya tenía una
  intención distinta no comunicada.

## 3. Convenciones del Proyecto

- Comandos de build/test reales (de `package.json` `"scripts"`, o de
  `CLAUDE.md`/`AGENTS.md`/`README.md`/`CONTRIBUTING.md` si documentan
  algo distinto a lo inferido).
- Convenciones de naming de archivos de test observadas en el repo.
- Restricciones explícitas del equipo (framework no soportado 1:1 por este
  skill, patrones prohibidos, etc.) detectadas en el Paso 0.

## 4. CI/CD

- Proveedor (`GitHub Actions`, `GitLab CI`, otro) y ubicación de los
  workflows relevantes a QA.
- Si ya existe una imagen con navegadores de Playwright preinstalados
  (relevante para `--skip-browsers` en `ensure-qa-dependencies.mjs`).

## 5. Entornos

- Entornos disponibles para pruebas (`staging`, `preprod`, etc.) y su
  `QA_BASE_URL` correspondiente (sin valores reales acá — solo el nombre
  del entorno; los valores viven en `.env.qa`, nunca en este archivo).

## 6. Historial de Decisiones Relevantes

Lista corta y append-only de decisiones que afectan cómo este skill debe
comportarse en este proyecto, con fecha — por ejemplo: "2026-03-10:
equipo decidió mantener Selenium Java para regresión hasta Q3, no migrar
antes", o "2026-05-02: se agregó Cypress component testing para el design
system, convive con Playwright E2E".

---

**Nunca escribir credenciales, tokens ni ningún valor de
`templates/env.example` en este archivo** — es contexto de proyecto, no
un lugar para secretos, y se trata con el mismo cuidado que cualquier otro
archivo bajo `resources/qa/` que podría terminar versionado por error.
