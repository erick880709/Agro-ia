# Patrones de API Testing (REST/GraphQL)

Este playbook define los criterios de API como disciplina propia: contratos, casos negativos, idempotencia,
paginación y compatibilidad de versiones — independiente de si hay una UI
que los ejercite.

---

## Índice

- [Cuándo Usar Este Playbook en Vez de (o Además de) E2E de UI](#cuándo-usar-este-playbook)
- [Validación de Contrato/Schema](#validación-de-contratoschema)
- [Casos Negativos](#casos-negativos)
- [Idempotencia](#idempotencia)
- [Paginación](#paginación)
- [Códigos de Error y Consistencia](#códigos-de-error-y-consistencia)
- [Compatibilidad de Versiones](#compatibilidad-de-versiones)
- [Estructura de un Caso de API](#estructura-de-un-caso-de-api)
- [Convención de Id de Caso](#convención-de-id-de-caso)

---

## Cuándo Usar Este Playbook

- El proyecto expone una API propia (REST/GraphQL) consumida por más de un
  cliente (web + mobile, o terceros) — un bug de contrato afecta a todos
  ellos, no solo a la UI web que este skill prueba por defecto.
- El caso a probar es más barato y más determinístico a nivel de API que
  simulando toda la interacción de UI (ej. validar 15 combinaciones de
  error de un formulario es más rápido y estable vía API que vía Playwright
  UI para cada una).
- Se necesita probar autorización real (ver
  `./security_testing_patterns.md#autorización-control-de-acceso`) — el
  control de acceso siempre se verifica a nivel de API, nunca solo de UI.

Conserva la herramienta API instalada. Para Karate aplica [su especialista](../../qa-ranger-karate/SKILL.md); si el proyecto ya usa Playwright, consulta [pruebas API con request](../../qa-ranger-playwright/references/05-api-testing.md).

## Validación de Contrato/Schema

Comparar la respuesta real contra el schema documentado (OpenAPI/JSON
Schema si existe) en vez de solo revisar campos sueltos:

Implementación: [ejemplo Playwright](../../qa-ranger-playwright/references/17-api-seguridad-fraude.md#api).

Si no existe un schema formal en el proyecto, generarlo a partir de la
respuesta real observada (con el equipo de backend) antes de automatizar
esta validación — no inventar un schema desde cero sin confirmarlo.

## Casos Negativos

Para cada endpoint que muta datos, cubrir como mínimo:

| Caso | Resultado esperado |
|---|---|
| Campo requerido faltante | 400 con mensaje que identifica el campo |
| Tipo de dato incorrecto (string donde se espera número) | 400, nunca un 500 |
| Valor fuera de rango (negativo, cero, excede máximo) | 400/422 |
| Payload vacío o malformado (JSON inválido) | 400 controlado |
| Recurso referenciado que no existe (FK inválida) | 404/422, no un 500 de constraint de base de datos |
| Método HTTP no soportado en la ruta | 405 |
| Content-Type incorrecto | 415 o manejo explícito |

## Idempotencia

Ver también `./adversarial_fraud_testing.md#categorías-de-abuso` para el caso
de abuso; acá el foco es el contrato correcto:

Implementación: [ejemplo Playwright](../../qa-ranger-playwright/references/17-api-seguridad-fraude.md#api).

Si el endpoint no soporta `Idempotency-Key`, documentarlo como riesgo en el
plan de pruebas — no asumir que el cliente nunca va a reintentar.

## Paginación

| Caso | Resultado esperado |
|---|---|
| Página fuera de rango (más allá del total) | Lista vacía, no error ni página 1 silenciosa |
| `pageSize`/`limit` excede el máximo permitido | Se aplica el máximo del servidor, documentado, no lo que pide el cliente sin límite |
| Item insertado/eliminado entre páginas | Comportamiento documentado (duplicado/salteado es aceptable si está documentado; si no, es un defecto) |
| Orden no especificado explícitamente | Resultado estable entre llamadas (no reordena aleatoriamente entre páginas) |

## Códigos de Error y Consistencia

Todos los endpoints del proyecto deberían devolver errores en una forma
consistente (mismo shape de body, mismo esquema de código de error interno
si existe). Un caso por endpoint que verifique el shape del error, no solo
el status code, detecta inconsistencias que rompen el manejo de errores del
cliente.

Implementación: [ejemplo Playwright](../../qa-ranger-playwright/references/17-api-seguridad-fraude.md#api).

## Compatibilidad de Versiones

Si la API versiona (`/v1/`, `/v2/`, header `Accept-Version`, etc.):

- Verificar que clientes viejos apuntando a una versión deprecada siguen
  funcionando durante el período de gracia documentado.
- Verificar que un campo nuevo agregado en `v2` no rompe el parseo de un
  cliente `v1` (aditivo, no rompe compatibilidad hacia atrás).
- Si se elimina o renombra un campo, confirmar que hay un plan de
  deprecación comunicado antes de tratarlo como "esperado" en las pruebas.

## Estructura de un Caso de API

Igual formato que `./markdown_test_runbook.md`, con estos campos
adicionales relevantes para API:

```markdown
## Caso de Prueba API-04 - Rechaza transferencia sin campo `amount`

- Prioridad: high
- Endpoint: POST /api/transfers
- Datos de prueba: payload sin `amount`, resto de campos válidos, `${QA_USER_TOKEN}`

### Resultado esperado
- Status 400
- Body: `{ "error": { "code": "MISSING_FIELD", "field": "amount" } }`
```

## Convención de Id de Caso

Usar el prefijo `API-` (ej. `API-01 [high]`), reconocido al leer el CTRF
(`../../../contracts/output/validators/qa/ctrf.mjs`). Para API conserva los resultados del runner según la [política común](evidence_guide.md). Video no aplica sin UI; trazas o logs adicionales dependen de la herramienta y del encargo.
