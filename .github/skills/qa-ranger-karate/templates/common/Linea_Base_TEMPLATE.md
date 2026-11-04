# Línea Base — {{PROYECTO}}

> Memoria del proyecto de pruebas. Leer al iniciar cada sesión; actualizar al cerrar un hito.
> No incluir secretos.

## Stack
| Elemento | Valor |
|---|---|
| Karate | {{KARATE_VERSION}} (línea {{LINEA}}) |
| Java | {{JAVA_VERSION}} |
| Build | {{BUILD}} |
| Runner CI | SuiteTest (paralelo, {{THREADS}} hilos) |
| Reportes | HTML + JUnit XML + Cucumber JSON |

## Ambientes
| Ambiente | baseUrl | Auth | Notas |
|---|---|---|---|
| dev | | | |
| qa  | | | |
| stg | | | |

## Autenticación
- Mecanismo: (OAuth2 client_credentials / bearer / mTLS / API key)
- Origen de credenciales: (variables de entorno, grupo de variables del pipeline)

## Convenciones
- Tags: nivel (`@smoke`, `@regresion`), dominio, tipo (`@negativo`, `@seguridad`, `@contrato`), estado (`@wip`, `@bug=`), trazabilidad (`@req=`).
- Nombres de escenario: `[HU-xxx][CA-n] comportamiento esperado`.
- Estructura: `src/test/java/<dominio>/{*.feature, schemas/, data/}`, helpers en `common/` con `@ignore`.

## Evidencia
- API: resultados originales del runner por caso; no se exige video.
- `QA_RUN_ID` del host o ID único; reportes en `resources/qa/reports/<runId>/karate-reports/`.
- Excepciones explícitas del encargo y motivo:

## Cobertura
| Servicio / endpoint | Estado | Escenarios | Pendiente |
|---|---|---|---|
| | | | |

## Decisiones
| Fecha | Decisión | Motivo |
|---|---|---|
| | | |

## Deuda y riesgos conocidos
-
