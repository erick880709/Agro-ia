# Formato de Runbook de Pruebas en Markdown

Usá este formato cuando la ejecución de pruebas esté dirigida por un documento Markdown.

## Secciones Obligatorias

1. Objetivo
- Qué se está validando y por qué.

2. Entorno
- URL base, nombre del entorno, navegador objetivo, y requisitos de seed/reseteo.
- **Roles** de cuentas de prueba únicamente (ej. "usuario estándar", "admin")
  — nunca usuarios/passwords reales. Apuntar a `../templates/env.example` y a las
  variables de entorno que necesita la ejecución (`QA_BASE_URL`,
  `QA_USER_EMAIL`, `QA_USER_PASSWORD`, etc.).
- Si esas variables no están definidas todavía, no es un bloqueante: correr
  `../scripts/ensure-test-user.mjs --role <rol>` genera credenciales de
  prueba nuevas y las provisiona (por API si hay `QA_SEED_API_URL`, o por
  el signup real de la app) antes de ejecutar el runbook.

3. Precondiciones
- Estado requerido de la aplicación antes de la ejecución.

4. Casos de Prueba
- Cada caso debe incluir:
  - Id de Caso (estable, único, patrón `TC-\d+`; nunca renumerar un caso
    existente una vez que ya tiene historial de ejecución). Para casos que
    pertenecen a un playbook especializado, usar el prefijo correspondiente
    en vez de `TC-` — mismo formato, mismas reglas, mismo pipeline de
    evidencia/manifest/veredicto:
    - `SEC-` seguridad funcional (`./security_testing_patterns.md`)
    - `FRAUD-` adversarial/anti-fraude (`./adversarial_fraud_testing.md`)
    - `API-` contrato/negativos de API (`./api_testing_patterns.md`)
    - `A11Y-` accesibilidad (`./accessibility_testing_guide.md`)
    - `PERF-` performance (`./performance_testing_guide.md` — evidencia
      distinta, ver ese reference, no produce CTRF)
  - Título
  - Prioridad (critical/high/medium/low)
  - Pasos
  - Resultado esperado
  - Datos de prueba (referencias a variables de entorno, ej.
    `${QA_USER_EMAIL}` — no secretos literales)
  - Grabación requerida (sí/no) — ver `./evidence_guide.md` para la
    política por defecto del proyecto (este skill usa "sí" por defecto para
    todos los casos)
  - Ruta del spec automatizado (se completa después de grabar, ej.
    `e2e/checkout-happy-path-TC-01.spec.ts`)

5. Reglas de Evidencia
- Qué artefactos son obligatorios para pass/fail (screenshots, trace, video, logs).
- Por defecto: video + trace + screenshot obligatorios para cada caso, no
  solo para los que fallan (ver `./evidence_guide.md`).

6. Criterios de Salida
- Condiciones para marcar GO, GO con riesgos, o NO-GO.

## Plantilla Recomendada de Caso

```markdown
## Caso de Prueba TC-01 - Login con credenciales válidas

- Prioridad: critical
- Grabación requerida: sí
- Ruta del spec automatizado: e2e/login-TC-01.spec.ts
- Datos de prueba:
  - Usuario: ${QA_USER_EMAIL} / ${QA_USER_PASSWORD}

### Pasos
1. Abrir /login.
2. Ingresar credenciales válidas.
3. Hacer clic en Ingresar.

### Resultado esperado
- El usuario es redirigido a /dashboard.
- El nombre del usuario es visible en el header.

### Evidencia
- Video del flujo completo (obligatorio, en cada ejecución).
- Screenshot después del login exitoso.
- Trace de Playwright.
```

## Reglas de Parseo para la Ejecución

- Parsear los encabezados como límites de caso cuando contienen un patrón
  de id de caso reconocido: `TC-`, `SEC-`, `FRAUD-`, `API-`, `A11Y-` o
  `PERF-`.
- Si dos casos del runbook usan el mismo id `TC-xxx` por error (copy-paste sin
  actualizar), corregirlo antes de ejecutar. Al leer el CTRF, un caso/proyecto
  duplicado rechaza la corrida; es mejor prevenirlo en el runbook.
- Si un caso no tiene resultado esperado, marcarlo como inválido y pedir aclaración.
- Si los datos de prueba de un caso parecen contener una credencial real
  (no una referencia `${ENV_VAR}`), detenerse y marcarlo en vez de ejecutar
  — no seguir adelante silenciosamente con un secreto filtrado.
- Si un caso está marcado como grabación requerida, crear o actualizar un
  spec de Playwright vinculado al mismo id de caso, con el id de caso (y
  opcionalmente una etiqueta `[prioridad]`) como prefijo literal del título
  de la prueba — ver `./evidence_guide.md#convención-de-id-de-caso`. Esto es
  lo que permite que el CTRF asocie el video resultante a este caso
  automáticamente.
- Ejecutar los casos críticos antes que los medium/low cuando el tiempo es limitado.
- Generar un `runId` por ejecución (timestamp o id de build de CI). Con Playwright,
  la evidencia queda en `resources/qa/<CASE-ID>/<runId>/<proyecto>/attempt-<n>/`;
  otros runners la dejan en `resources/qa/test-results/<runId>/`. El CTRF queda en
  `resources/qa/reports/<runId>/ctrf.json`, sin pisar ejecuciones anteriores.
- Este runbook en sí mismo se guarda como
  `resources/qa/runbooks/qa-runbook-<feature>.md` (creando la carpeta si no existe).

## Esquema del Reporte Final de Ejecución

Se genera automáticamente con
`node .claude/contracts/output/generate-execution-report.mjs --ctrf resources/qa/reports/<runId>/ctrf.json --expected <casos.json> --out resources/qa/reports/<runId>/execution-report.md`,
donde `<casos.json>` es la lista `{id, project, priority}` de los casos de este runbook.
En CI, sumar `--fail-on-no-go` para que el veredicto bloquee el pipeline en vez
de quedar solo como texto informativo.

Para cada id de caso, incluye:
- Estado: passed, failed, blocked, o not-run
- Resumen del defecto (primera línea del error de fallo, si falló o fue bloqueado)
- Rutas de los artefactos de evidencia (nombres de archivo de video/trace/screenshot)
- Ruta de la grabación, tomada de los adjuntos del caso en el CTRF

Más un veredicto a nivel de ejecución: `GO`, `GO with known risks`, o
`NO-GO` (cualquier caso etiquetado `[critical]` que falle fuerza `NO-GO`).
