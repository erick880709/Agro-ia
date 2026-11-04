# Pruebas y validación en Angular

## Descubrir el runner y los comandos

No asumas Vitest ni Karma: proyectos v22 siguen usando Karma/Jasmine con zone.js
y proyectos antiguos ya migraron a Jest. Identifica por proyecto:

| Señal en `angular.json`/`project.json` | Runner |
|---|---|
| `@angular/build:unit-test` (opción `runner`, por defecto `vitest`) | Vitest o Karma vía el builder unificado |
| `@angular-devkit/build-angular:karma` o `@angular/build:karma` | Karma + Jasmine |
| `@angular-builders/jest`, `@nx/jest` | Jest |
| `@nx/vite:test`, `@analogjs/vitest-angular` | Vitest con Vite |

Usa los scripts de `package.json` y los targets existentes (`test`, `lint`,
`build`, `e2e`, `nx affected`). `angular_toolkit.py discover` los lista.

## Escalera de validación

Del más barato al más caro; acota al proyecto y a las specs afectadas.

| Paso | Comando fallback (binario local) | Cuándo |
|---|---|---|
| Tipos | `tsc -p tsconfig.app.json --noEmit` y `tsc -p tsconfig.spec.json --noEmit` | Siempre. No valida plantillas |
| Lint | `ng lint <proyecto>` | Si existe target de lint; no lo añadas |
| Tests focalizados | Vitest unificado: `ng test <proyecto> --watch=false --include <glob>`; Karma: `--watch=false --browsers=ChromeHeadless --include <glob>`; Jest: el script del proyecto con el patrón | Por incremento |
| Tests del proyecto | Mismo comando sin `--include` | Al cerrar |
| Build | `ng build <proyecto>` (producción) con `--output-path` temporal | Si cambian rutas, lazy loading, configuración, estilos globales o dependencias: valida plantillas en AOT y **presupuestos** |
| Nx | `nx affected -t lint test build` o el target equivalente | En workspaces Nx, en lugar de `./...` manual |
| E2E | `ng e2e` o el script existente | Solo si el framework ya está configurado y hay entorno aislado |
| API inestable | `angular_toolkit.py unstable` | Si añadiste imports de `@angular/*` |

`angular_toolkit.py validate [--include glob] [--build]` ejecuta tipos, lint,
tests y build opcional con binarios locales, sin instalar nada, sin escribir el
`dist/` del proyecto y con salida sin códigos de color, en filas
`passed/failed/not_run`.

Un exceso de presupuesto es un fallo de build, no una advertencia que se pueda
subir en `angular.json` para cerrar el cambio: elevar un presupuesto es una
decisión con dueño.

## Pruebas que demuestran comportamiento

- Prueba lo observable: DOM renderizado (texto, atributos, roles ARIA), outputs
  emitidos, peticiones HTTP y navegación; no propiedades privadas ni que un
  método "fue llamado" cuando el efecto es verificable.
- Selecciona elementos por rol, etiqueta o `data-testid` según la convención; no
  por clases de estilo.
- Inputs de señal: `fixture.componentRef.setInput('nombre', valor)`; no asignes
  propiedades del componente.
- **Zoneless** (default en apps v21+, sin zone.js): patrón Actuar → Esperar →
  Afirmar con `await fixture.whenStable()`. No uses `fixture.detectChanges()`
  como mecanismo principal ni `markForCheck()` para forzar vistas. `fakeAsync`/
  `tick` dependen de zone.js.
- **Con zone.js** (Karma/Jasmine tradicional): `fakeAsync`/`tick`/`flush` y
  `detectChanges()` siguen siendo válidos; sigue el patrón del archivo de
  spec existente.
- HTTP: `provideHttpClient()` + `provideHttpClientTesting()` y
  `HttpTestingController` (`expectOne`, `flush`, `verify`); con
  `withInterceptors` si pruebas interceptores. No uses `HttpClientTestingModule`
  en código nuevo si el proyecto ya usa providers.
- Rutas: `RouterTestingHarness` y `provideRouter(rutas)`; guards funcionales con
  `TestBed.runInInjectionContext`.
- Componentes complejos de librería: harnesses del CDK/Material si el proyecto
  los usa.
- Dobles: `{ provide: Servicio, useValue: fake }` con solo lo que el componente
  consume; no mockees el propio componente bajo prueba.
- Suscripciones y fugas: para componentes con Observables, comprueba tras
  `fixture.destroy()` que la fuente ya no tiene suscriptores (`subject.observed`).
- Formularios: escribe en el input real (`value` + evento `input`) y envía el
  formulario; prueba válidos, inválidos y que no se emita con datos inválidos.
- Una spec generada por `ng generate` con solo `should create` no es evidencia
  de comportamiento.

## Comprobar que la prueba puede fallar

Para un bug, la spec nueva debe fallar en la versión inicial por la aserción del
defecto. Para lógica crítica, aplica una mutación controlada en un workspace
aislado (quitar el `track`, eliminar la cancelación de la suscripción, relajar
un validador, cambiar la comparación de origen del interceptor) y confirma que
la spec la detecta; revierte después.

## Contexto de la evidencia

Registra versión instalada de Angular, Node, runner y navegador (o jsdom),
zoneless o zone.js, proyecto y specs ejecutadas, configuración de build y la
revisión validada. Distingue: API real frente a `HttpTestingController` o mock
server (una prueba con dobles no demuestra compatibilidad con el backend real),
fallos preexistentes, regresiones y entorno faltante (navegador, dependencias).
