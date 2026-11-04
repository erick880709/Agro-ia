# Línea Base — __NOMBRE__

> Memoria del proyecto de pruebas UI. Leer al iniciar cada sesión; actualizar al cerrar un hito. Sin secretos.

## Stack
| Elemento | Valor |
|---|---|
| Selenium | __SELENIUM__ |
| Lenguaje / runner | __STACK__ |
| Navegadores | chrome (headless) |
| Infraestructura | local + docker-selenium en CI |
| Reportes | JUnit XML + evidencia en fallos |

## Ambientes
| Ambiente | baseUrl | Usuarios de prueba | Notas |
|---|---|---|---|
| __ENV__ | __BASE_URL__ | | |

## Autenticación
- Mecanismo:
- Origen de credenciales: variables de entorno E2E_USER / E2E_PASSWORD (secretos del pipeline)

## Convenciones
- Localizadores: id/name/data-testid > CSS semántico > XPath por texto. Sin XPath absolutos ni clases generadas.
- Solo esperas explícitas; implicitlyWait = 0; sin sleep.
- Nombres: `[HU-xxx][CA-n] comportamiento esperado`.
- Tags/markers: smoke, regresion, dominio.

## Cobertura
| Flujo / pantalla | Estado | Tests | Pendiente |
|---|---|---|---|
| | | | |

## Decisiones
| Fecha | Decisión | Motivo |
|---|---|---|

## Deuda, flaky conocidos y riesgos
-
