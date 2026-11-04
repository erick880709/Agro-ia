# Línea Base — __NOMBRE__

> Memoria del proyecto de pruebas Robot Framework. Leer al iniciar cada sesión; actualizar al cerrar un hito. Sin secretos.

## Stack
| Elemento | Valor |
|---|---|
| Robot Framework | __RF__ (mínimo soportado por el agente: __RF_MAJOR__.x) |
| Perfil / librerías | __STACK__ |
| Python | 3.12 (local) · versión del agente de CI: |
| Ejecución | `./ejecutar.sh __ENV__` · CI: __CI__ |
| Reportes | output.xml + log/report HTML + xunit.xml + CTRF (`resources/qa/reports/<runId>/ctrf.json`) |

## Ambientes
| Ambiente | Archivo de variables | Destino (URL / host sin credenciales) | Notas |
|---|---|---|---|
| __ENV__ | `__VARFILE__` | __BASE_URL__ | |

## Credenciales y variables de entorno
- Origen: secretos del pipeline / `.env.qa` local (ignorado por git).
- Nombres exactos (Linux distingue mayúsculas): __ENV_VARS__

## Convenciones
- Nombre de test: `TC-01 [critical] [HU-xxx][CA-n] comportamiento`; ID también como tag para seleccionar (`--include TC-01`).
- Keywords de usuario en `resources/`, Title Case, sin lógica en el cuerpo del test.
- Sin `Sleep`; esperas por condición. Sin SQL destructivo contra ambientes compartidos.
- Tags: smoke, regresion, dominio.

## Cobertura
| Flujo / tabla / endpoint | Estado | Casos | Pendiente |
|---|---|---|---|
| | | | |

## Decisiones
| Fecha | Decisión | Motivo |
|---|---|---|

## Deuda, flaky conocidos y riesgos
-
