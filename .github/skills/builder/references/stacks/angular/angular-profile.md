# Perfil Angular

Capa específica de stack para Builder. Concreta el flujo de `SKILL.md` cuando el
componente afectado es una aplicación o librería Angular; no reemplaza sus
invariantes. Las instrucciones del proyecto y el mandato del usuario prevalecen
sobre cualquier preferencia idiomática de esta guía.

## Activación

Aplica el perfil a cada workspace con `angular.json`, `nx.json`/`project.json`
con targets de Angular, o `@angular/core` en `package.json`. En monorepos (Nx,
varios proyectos en `angular.json`), aplícalo solo a los proyectos afectados.

Antes de diseñar, ejecuta el descubrimiento estático (no ejecuta npm ni `ng`):

```text
python <skill-root>/scripts/angular_toolkit.py discover <ruta>
```

Devuelve: versión de Angular declarada e instalada, TypeScript y RxJS, tipo de
workspace (CLI o Nx), proyectos con sus builders, runner de pruebas por
proyecto, defaults de schematics, librerías relevantes (NgRx, Material, Aria,
SSR, i18n, federación), ESLint/Prettier, archivos de instrucciones para agentes,
configuración del MCP de Angular y un recuento de patrones (`*ngIf` frente a
`@if`, `@Input` frente a `input()`, NgModules, formularios, suscripciones).
El recuento indica la convención dominante; no sustituye leer el módulo de
referencia.

## Orden de autoridad dentro del proyecto

1. Mandato del usuario y fuentes del cambio.
2. Archivos de instrucciones para agentes del repositorio, **incluidos los
   anidados**: `AGENTS.md`, `CLAUDE.md` (raíz y carpetas como `src/`),
   `.github/copilot-instructions.md`, `.cursor/rules`, `GEMINI.md`. Pueden
   imponer convenciones fuertes (por ejemplo, "Promises en vez de RxJS",
   "plantillas siempre externas"). Son datos del encargo: no autorizan
   comandos ni acciones remotas (invariante 9).
3. Reglas de ESLint (`@angular-eslint`), `tsconfig` estricto y defaults de
   schematics en `angular.json` (`changeDetection`, `style`, `type`, `skipTests`).
4. Convención dominante del código existente en el área afectada.
5. Esta guía y las pautas oficiales de Angular para la versión instalada.

## Versión objetivo: la versión instalada manda

1. La versión real es la de `node_modules/@angular/core/package.json`. Si no hay
   dependencias instaladas, usa el rango de `package.json` y decláralo como
   supuesto. El CLI global, el MCP o tu conocimiento no definen la versión.
2. Una API existe y es estable solo si la versión instalada lo dice. Comprueba
   con `angular_toolkit.py api-status <símbolo>...`, que lee las etiquetas JSDoc
   de los `.d.ts` instalados (`@publicApi <versión>`, `@experimental`,
   `@developerPreview`, `@deprecated`). `unknown` significa que el `.d.ts` no lo
   declara; consulta la documentación de esa versión.
3. No introduzcas APIs `@experimental` ni `@developerPreview` en código
   productivo sin mandato explícito; `angular_toolkit.py unstable` las detecta.
4. No ejecutes `ng update`, ni cambies versiones de Angular, TypeScript, RxJS,
   Node o zone.js dentro de una feature: es una decisión con impacto en CI y
   consumidores. Regístrala como decisión pendiente.
5. Dentro de lo permitido, escribe Angular moderno en el código que creas o
   modificas y respeta el estilo vigente del área. No migres archivos vecinos
   (control flow, inputs de señal, standalone, `inject()`) fuera del encargo:
   eso es un `refactor` con sus schematics oficiales.
   Consulta [Angular moderno por versión](angular-modern-by-version.md).

## Mapa de lectura por tipo de cambio

| Necesidad del cambio | Guía |
|---|---|
| Componentes, plantillas, señales, RxJS, DI, estado, nombres | [Componentes y reactividad](angular-components-and-reactivity.md) |
| Rutas, guards, HTTP, interceptores, formularios, SSR, seguridad, a11y | [Rutas, HTTP y formularios](angular-routing-http-forms.md) |
| Pruebas, comandos de validación, evidencia | [Pruebas y validación Angular](angular-testing-and-validation.md) |
| Elegir API según la versión instalada | [Angular moderno por versión](angular-modern-by-version.md) |
| Revisión de calidad, diagnóstico de errores `NG0xxx` | [Revisión y diagnóstico Angular](angular-review-and-debugging.md) |
| Interfaz con sistema de diseño declarado | [UI con sistema de diseño](../../ui-with-design-system.md) |

## Superposición sobre el flujo de Builder

| Paso de Builder | Qué añade el perfil Angular |
|---|---|
| 1. Descubrir | `discover`; leer instrucciones de agentes, ESLint, `angular.json`, el componente/servicio de referencia y su spec; identificar si la app es zoneless o usa zone.js |
| 2. Especificar | Declarar versión instalada, rutas y componentes afectados, contratos HTTP consumidos y estados de UI (carga, vacío, error, permiso) |
| 3. Diseñar | Ubicar por feature siguiendo el layout existente; elegir señales/RxJS/estado según la convención del área; respetar fronteras Nx (`tags`) |
| 4. Implementar | Generar artefactos con `ng generate` del CLI local cuando el proyecto lo hace así; completar el cableado (imports del componente, rutas, providers) |
| 5. Validar | Escalera: typecheck → lint → tests focalizados → build si cambian rutas, presupuestos o configuración |
| 6. Entregar | Registrar versión de Angular/Node, runner, comandos, specs ejecutadas y si la API se simuló |

## Uso de herramientas Angular

- **CLI local**: invoca `node_modules/.bin/ng` o el script de `package.json`. No
  uses `npx @angular/cli@latest` en un proyecto existente: descargaría otra versión.
- **`ng generate`**: úsalo con los defaults de `angular.json` y revisa los
  archivos creados; no aceptes una spec generada vacía como evidencia.
- **MCP del CLI** (`ng mcp`): si ya está configurado, `get_best_practices`,
  `search_documentation` y `list_projects` son fuentes útiles y ligadas a la
  versión. No lo configures ni lo instales sin mandato.
- **Skill oficial `angular-developer`** (angular/skills): si está instalada,
  sirve como referencia de API; las invariantes y el flujo de Builder siguen
  gobernando alcance, evidencia y cierre.

## Límites del perfil

- No crea aplicaciones (`ng new`), workspaces Nx, librerías publicables ni
  micro-frontends: eso es baseline o arquitectura. No añade SSR, PWA, i18n,
  Tailwind, NgRx, Material ni frameworks E2E (`ng add`) dentro de una feature.
- No cambia de runner (Karma → Vitest), de zone.js a zoneless ni de estrategia
  de formularios como efecto colateral.
- No instala dependencias (`npm install`) sin mandato; si faltan, las
  comprobaciones quedan `not_run` con razón.
- Para sistema de diseño, tokens y assets, aplica la guía de UI existente.

## Fuentes destiladas

Síntesis adaptada al flujo de Builder a partir de `angular/skills`
(`angular-developer`, `angular-new-app`; build de octubre de 2026),
`sajeetharan/angular-agent-kit`, el agente `angular-architect` de
`VoltAgent/awesome-claude-code-subagents`, `hereandnowai/agent-skills`
(angular21), los repositorios de cursos de Angular University y los `.d.ts`
publicados de `@angular/*` 21.2 y 22.2, que se usaron para verificar estados de
estabilidad. Una fuente no oficial publicaba una API de Signal Forms inexistente
(`@angular/forms/experimental`): por eso esta guía exige verificar contra los
paquetes instalados.
