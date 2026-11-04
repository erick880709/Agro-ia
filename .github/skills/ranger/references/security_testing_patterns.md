# Patrones de Security Testing para Aplicaciones React/Next.js

Guía para diseñar y ejecutar pruebas de seguridad funcional (no un pentest
completo) usando el mismo pipeline de casos/evidencia/veredicto que el resto
de este skill. Cubre lo que un QA senior puede validar sin herramientas de
pentesting especializadas: autenticación, autorización, sesión, superficie
de API y exposición de secretos.

---

## Índice

- [Alcance y Límites](#alcance-y-límites)
- [Autenticación](#autenticación)
- [Autorización (Control de Acceso)](#autorización-control-de-acceso)
- [Gestión de Sesión](#gestión-de-sesión)
- [Seguridad de API](#seguridad-de-api)
- [Exposición de Secretos y Datos Sensibles](#exposición-de-secretos-y-datos-sensibles)
- [Cabeceras de Seguridad](#cabeceras-de-seguridad)
- [Convención de Id de Caso](#convención-de-id-de-caso)
- [Cuándo Escalar a un Pentest Real](#cuándo-escalar-a-un-pentest-real)

---

## Alcance y Límites

Este playbook valida **comportamiento observable desde afuera de la
aplicación** (como lo haría un usuario malicioso con acceso normal), no
vulnerabilidades de infraestructura, criptografía o código fuente. No
reemplaza un pentest formal ni un escaneo SAST/DAST — es la capa de QA que
detecta regresiones de seguridad funcional antes de que lleguen a un
pentest o a producción.

**Nunca ejecutar este playbook contra un entorno de producción real ni
contra sistemas que no sean explícitamente del proyecto bajo prueba.**
Confirmar el entorno objetivo (`QA_BASE_URL`) antes de correr cualquier
caso de este playbook — igual que con el resto de este skill, nunca contra
`prod` salvo pedido explícito y con el veredicto documentado como
"verificación en producción", no como "pruebas de seguridad".

## Autenticación

Casos a cubrir (adaptar al mecanismo real del proyecto: password, OAuth,
magic link, MFA):

| Escenario | Resultado esperado |
|---|---|
| Login con credenciales inválidas repetidas | Rate limiting o bloqueo temporal tras N intentos; sin diferenciar "usuario no existe" de "password incorrecta" en el mensaje |
| Enumeración de usuarios vía signup/recuperación | El mensaje de error no confirma si un email ya está registrado |
| Acceso a rutas protegidas sin sesión | Redirección a login, nunca contenido parcial ni un flash de datos protegidos |
| Reutilización de token expirado | Rechazado con 401, sin refrescar silenciosamente sin validación |
| Password débil en signup (si aplica política) | Rechazado con mensaje claro, no solo validación de cliente |

Implementación: [ejemplo Playwright](../../qa-ranger-playwright/references/17-api-seguridad-fraude.md#seguridad-funcional).

## Autorización (Control de Acceso)

El error más común y más costoso: validar el rol en el cliente (ocultar un
botón) pero no en el servidor/API. Todo caso de autorización debe probarse
**a nivel de API**, no solo de UI — ocultar un botón no es control de
acceso.

| Escenario | Resultado esperado |
|---|---|
| Usuario estándar accede a ruta/endpoint de admin por URL directa | 403/redirección, no solo el link oculto en el menú |
| Usuario A accede a un recurso de Usuario B por id (IDOR) | 403/404, nunca el recurso ajeno |
| Rol degradado accede a acción antes permitida | Acceso revocado inmediatamente, no cacheado en el cliente |
| Llamada directa a la API que respalda una acción oculta en la UI | Rechazada igual que si el botón existiera |

Implementación: [ejemplo Playwright](../../qa-ranger-playwright/references/17-api-seguridad-fraude.md#seguridad-funcional).

Para cubrir esto sistemáticamente: construir una matriz rol × recurso ×
acción (ver `./requirements_analysis_guide.md` para cómo extraerla de los
requisitos) y generar un caso por combinación que debería estar denegada.

## Gestión de Sesión

| Escenario | Resultado esperado |
|---|---|
| Logout invalida la sesión del lado del servidor | El token/cookie ya no sirve para llamadas posteriores, no solo se borra del cliente |
| Cookie de sesión | `HttpOnly`, `Secure`, `SameSite=Lax` o `Strict` según el flujo |
| Cambio de password | Invalida sesiones activas en otros dispositivos (si el producto lo promete) |
| Sesión inactiva | Expira según la política documentada, no indefinidamente |
| Fijación de sesión (session fixation) | Se emite un id de sesión nuevo después del login, no se reutiliza el anónimo previo |

## Seguridad de API

Complementa `./api_testing_patterns.md` — acá el foco es abuso, no
contrato funcional.

| Escenario | Resultado esperado |
|---|---|
| Payload con campos extra no documentados (mass assignment) | Ignorados o rechazados, nunca aplicados silenciosamente (ej. `"role": "admin"` en un signup) |
| Content-Type inesperado o payload malformado | 400 controlado, nunca un stack trace ni un 500 |
| Rate limiting en endpoints sensibles (login, reset password, OTP) | Aplicado y verificable con respuesta 429 |
| CORS | Solo orígenes esperados en `Access-Control-Allow-Origin`, nunca `*` en endpoints autenticados |

## Exposición de Secretos y Datos Sensibles

| Escenario | Resultado esperado |
|---|---|
| Respuestas de API con datos de otros usuarios en errores | Mensajes de error genéricos, sin volcar el objeto completo |
| Bundle de frontend / source maps en producción | Sin claves de API ni secretos hardcodeados (grep del bundle buildeado) |
| LocalStorage/sessionStorage | Sin tokens de larga vida ni PII sensible sin necesidad |
| Logs de consola en producción | Sin tokens, passwords, ni PII |

```bash
# Grep rápido de secretos evidentes en el bundle de producción antes de un release
grep -rEi "(api[_-]?key|secret|password)\s*[:=]\s*['\"][a-z0-9]{16,}" .next/static/ 2>/dev/null
```

## Cabeceras de Seguridad

Comprueba las cabeceras del documento principal según los requisitos y el entorno objetivo:

Implementación: [ejemplo Playwright](../../qa-ranger-playwright/references/17-api-seguridad-fraude.md#seguridad-funcional).

## Convención de Id de Caso

Usar el prefijo `SEC-` (ej. `SEC-01`, `SEC-02 [critical]`) para que el
CTRF (`../../../contracts/output/validators/qa/ctrf.mjs`) identifique la evidencia por separado de los
casos funcionales, siguiendo la misma convención de
`./markdown_test_runbook.md`. Un runbook de seguridad es un runbook normal
con casos `SEC-xxx` en vez de `TC-xxx` — mismas reglas de credenciales,
evidencia y veredicto.

## Cuándo Escalar a un Pentest Real

Detenerse y recomendar un pentest/revisión de seguridad especializada
(no seguir generando casos de este playbook) cuando aparezca:

- Un hallazgo que ya confirma acceso no autorizado real a datos de
  producción (no solo un caso de prueba diseñado para verificarlo).
- Necesidad de probar infraestructura (red, WAF, cloud IAM) — fuera del
  alcance de este skill, que trabaja a nivel de aplicación.
- Requisitos de cumplimiento formal (PCI-DSS, ISO 27001) que requieren un
  reporte de un tercero certificado.

En esos casos, documentar el hallazgo con severidad y evidencia (igual que
cualquier defecto) y marcarlo explícitamente como "requiere pentest/revisión
de seguridad formal" en el reporte de ejecución, en vez de intentar
cerrarlo solo con este skill.
