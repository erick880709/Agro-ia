# Línea Base — {{NOMBRE}}

> Memoria del proyecto de pruebas E2E. Leer al iniciar cada sesión; actualizar al cerrar un hito.
> Sin secretos.

## Stack
| Elemento | Valor |
|---|---|
| Playwright | {{PLAYWRIGHT_VERSION}} |
| Node | 22 LTS |
| Lenguaje | TypeScript |
| Navegadores / proyectos | {{PROYECTOS}} |
| Runner CI | {{CI}} |
| Reportes | HTML + JUnit + JSON (trazabilidad) |

## Ambientes
| Ambiente | baseURL | Usuarios de prueba | Notas |
|---|---|---|---|
| dev | | | |
| qa  | | | |
| stg | | | |

## Autenticación
- Mecanismo: (formulario / API / SSO / MFA — cómo se resuelve en pruebas)
- Roles y archivos de storageState:
- Origen de credenciales: (.env local, variable group / secrets del pipeline)

## Convenciones
- Locators: getByRole > getByLabel > getByPlaceholder > getByText > getByTestId (atributo: `data-testid`). Sin XPath.
- Títulos: `[HU-xxx][CA-n] comportamiento esperado`.
- Tags: `@smoke`, `@regresion`, `@visual`, `@a11y`, dominio (`@pagos`), `@cuarentena`.
- Estructura: `pages/` (POM), `fixtures/`, `api/` (clientes para setup), `tests/<dominio>/`.

## Evidencia
- Política browser predeterminada: video, trace y screenshot en cada caso, incluidos los exitosos y CI.
- Corrida: `QA_RUN_ID` del host o ID único; evidencia organizada en `resources/qa/<CASE-ID>/<runId>/<proyecto>/attempt-<n>/`, originales en `resources/qa/test-results/<runId>/`, reportes en `resources/qa/reports/<runId>/`.
- Excepciones explícitas del encargo y motivo:

## Cobertura
| Flujo / pantalla | Estado | Tests | Pendiente |
|---|---|---|---|
| | | | |

## Decisiones
| Fecha | Decisión | Motivo |
|---|---|---|
| | | |

## Deuda, flaky conocidos y riesgos
-
