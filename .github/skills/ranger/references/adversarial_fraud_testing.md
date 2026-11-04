# Testing Adversarial y Anti-Fraude

Guía para diseñar casos de prueba con **mentalidad hostil**: en vez de
verificar que el camino feliz funciona, intentar activamente romper
invariantes de negocio (duplicar una transacción, escalar un privilegio,
corromper un estado) de la misma forma en que lo intentaría un usuario
malicioso o un flujo de fraude real. Complementa
`./security_testing_patterns.md` (que cubre auth/autorización/sesión) con
foco en **reglas e invariantes de negocio**, no en el mecanismo de acceso.

Especialmente relevante en dominios financieros/transaccionales, donde el
costo de un caso no cubierto no es solo un bug sino una pérdida de dinero
real o un incidente regulatorio.

---

## Índice

- [Mentalidad Adversarial](#mentalidad-adversarial)
- [Categorías de Abuso](#categorías-de-abuso)
- [Cómo Derivar Casos desde las Reglas de Negocio](#cómo-derivar-casos-desde-las-reglas-de-negocio)
- [Patrones de Implementación en Playwright](#patrones-de-implementación-en-playwright)
- [Reporte de Hallazgos](#reporte-de-hallazgos)
- [Límites Éticos y Operativos](#límites-éticos-y-operativos)

---

## Mentalidad Adversarial

Antes de escribir un caso, para cada flujo crítico preguntarse:

1. **¿Qué pasa si repito esta acción?** (doble clic, doble submit, replay de request)
2. **¿Qué pasa si la hago dos veces en paralelo?** (race condition sobre el mismo recurso)
3. **¿Qué pasa si la interrumpo a la mitad?** (cierro la pestaña, pierdo la red, el timeout expira)
4. **¿Qué pasa si mando un valor que la UI no permite pero la API sí acepta?** (negativo, cero, fuera de rango, tipo incorrecto)
5. **¿Qué pasa si cambio el orden de los pasos?** (confirmar antes de validar, pagar antes de reservar el inventario)
6. **¿Qué pasa si uso el mismo recurso desde dos sesiones/roles a la vez?**

Esto no es testing exploratorio libre: cada pregunta que produce un
comportamiento indebido se convierte en un caso reproducible con el mismo
formato que el resto del runbook (id de caso, pasos, resultado esperado,
evidencia).

## Categorías de Abuso

| Categoría | Qué buscar | Ejemplo típico en banca/fintech |
|---|---|---|
| **Duplicación de transacciones** | Doble envío, doble clic, reintento automático del cliente | Doble clic en "Transferir" genera dos transferencias en vez de una |
| **Condiciones de carrera** | Dos operaciones concurrentes sobre el mismo saldo/recurso | Dos transferencias simultáneas desde una cuenta con saldo justo para una sola, ambas pasan |
| **Bypass de límites** | Límites de monto/frecuencia validados solo en el cliente | Editar el payload de la API para superar el límite diario mostrado en la UI |
| **Manipulación de estado** | Saltar pasos de un flujo multi-paso llamando directamente a un endpoint posterior | Confirmar un pago sin haber pasado por la validación de OTP |
| **Idempotencia rota** | Reintentos de red (timeout del cliente) duplican el efecto en el servidor | Un timeout en el cliente durante un pago, seguido de un reintento automático, cobra dos veces |
| **Manipulación de sesión/identidad** | Cambiar un id de recurso/usuario en el request sin cambiar la sesión | Cambiar el `accountId` en el payload de una transferencia a una cuenta que no es la del usuario logueado |
| **Abuso de flujos de recuperación** | Reset de password/2FA usado para tomar control de una cuenta | Flujo de recuperación no valida suficientemente la identidad antes de permitir un cambio de password |
| **Manipulación de montos/precisión** | Valores negativos, decimales, overflow, redondeo | Transferir un monto negativo revierte la dirección del movimiento de dinero |

## Cómo Derivar Casos desde las Reglas de Negocio

1. Tomar la matriz funcional del plan de pruebas (`../../qa-ranger-plan-pruebas/templates/test_plan_template.md`,
   sección 4) y, para cada regla de negocio explícita ("no se puede transferir
   más del saldo disponible", "un pago no puede confirmarse dos veces"),
   escribir el caso que **intenta violar la regla**, no solo el que la respeta.
2. Usar `./requirements_analysis_guide.md` para detectar invariantes
   implícitos que el requisito no menciona explícitamente pero que el
   negocio asume (ej. "un cupón no puede aplicarse dos veces" casi nunca
   está escrito, pero siempre se asume).
3. Priorizar por impacto económico/regulatorio, no solo por probabilidad —
   un caso de baja probabilidad pero alto impacto (duplicar una transferencia)
   se prueba igual que uno crítico de autenticación.

## Patrones de Implementación en Playwright

**Doble submit / doble clic:**

Implementación: [ejemplo Playwright](../../qa-ranger-playwright/references/17-api-seguridad-fraude.md#fraude-e-invariantes).

**Condición de carrera (dos requests concurrentes vía API):**

Implementación: [ejemplo Playwright](../../qa-ranger-playwright/references/17-api-seguridad-fraude.md#fraude-e-invariantes).

**Bypass de límite editando el payload directamente (sin pasar por la UI):**

Implementación: [ejemplo Playwright](../../qa-ranger-playwright/references/17-api-seguridad-fraude.md#fraude-e-invariantes).

**Saltar un paso de un flujo multi-etapa:**

Implementación: [ejemplo Playwright](../../qa-ranger-playwright/references/17-api-seguridad-fraude.md#fraude-e-invariantes).

## Reporte de Hallazgos

Un caso adversarial que **encuentra** el comportamiento indebido no es un
"fail" cualquiera: documentarlo con:

- Severidad de negocio (no solo técnica): impacto monetario estimado,
  reversibilidad, si es explotable en producción hoy.
- Reproducibilidad exacta (payload, timing, condiciones de carrera —
  conservar los artefactos diagnósticos reales del runner).
- Si el hallazgo implica que el bug ya podría estar siendo explotado en
  producción, escalarlo de inmediato fuera del ciclo normal de QA — no
  esperar al reporte de fin de ejecución.

Un caso adversarial `[critical]` que falla (es decir, que logra el abuso)
fuerza `NO-GO` igual que cualquier otro caso crítico — ver
`./markdown_test_runbook.md#esquema-del-reporte-final-de-ejecución`.

## Convención de Id de Caso

Usar el prefijo `FRAUD-` para casos de esta categoría (ej. `FRAUD-01
[critical]`), reconocido al leer el CTRF (`../../../contracts/output/validators/qa/ctrf.mjs`) igual que
`TC-`/`SEC-`/`API-`.

## Límites Éticos y Operativos

- Ejecutar únicamente contra entornos de prueba/staging con datos
  sintéticos — nunca contra producción ni con cuentas/datos reales de
  clientes.
- No usar datos de tarjetas, cuentas o identidades reales, ni siquiera
  parcialmente reales, en ningún caso de este playbook.
- Si el proyecto tiene un equipo de fraude/seguridad dedicado, coordinar
  con ellos antes de ejecutar en un entorno compartido — un caso de race
  condition puede generar alertas o datos ruidosos para otros sistemas de
  monitoreo.
