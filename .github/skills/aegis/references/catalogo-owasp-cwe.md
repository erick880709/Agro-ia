# Catálogo OWASP / CWE para la caza

Taxonomías de referencia (verifica la versión vigente si hay red; regístrala en el
reporte): **OWASP Top 10:2025**, **OWASP API Security Top 10:2023**, **OWASP Top 10 for
LLM Applications 2025** y **OWASP Top 10 for Agentic Applications 2026** (la misma que
usa archi en `19.1`). Cada hallazgo lleva `cwe` y `owasp_category` cuando aplique.

## Tabla de contenido

1. OWASP Top 10:2025 — qué buscar
2. OWASP API Security Top 10:2023
3. LLM y Agentic (resumen; detalle en ia-agentes-mcp.md)
4. CWE frecuentes y su sumidero típico

## 1. OWASP Top 10:2025

### A01 Control de acceso roto (CWE-639, 284, 285, 862, 863, 22, 918)
- ID tomado de path/body/query usado en consulta sin filtro de dueño/tenant (IDOR/BOLA).
- Endpoint nuevo fuera de la cadena de seguridad, o sin la anotación/regla que tienen sus vecinos.
- Autorización en cliente (guard de Angular) sin equivalente en servidor.
- Mass assignment: DTO de entrada con `role`, `status`, `ownerId`, `approvedAmount`.
- Path traversal en descargas/cargas; SSRF (incluida aquí en 2025) con URL derivada de entrada.

### A02 Configuración insegura (CWE-16, 1188, 489, 942)
- Defaults *fail-open*: `getenv("REQUIRE_AUTH","false")`, CORS por defecto `*`, debug activo.
- Actuators/pprof/swagger expuestos sin auth en perfiles productivos.
- Cabeceras de seguridad ausentes en respuestas HTML (nota de hardening salvo impacto trazado).
- Errores con stack trace o detalles internos al cliente.

### A03 Fallos de la cadena de suministro de software (CWE-1104, 829, 494)
- Dependencias con CVE alcanzable, abandonadas, typosquatting, repositorios no oficiales.
- Versiones dinámicas (`+`, `latest`, `^` sin lockfile), actions sin pinear por SHA.
- Scripts de instalación (`postinstall`) y binarios descargados sin verificación.
→ [cadena de suministro](cadena-suministro-y-secretos.md)

### A04 Fallos criptográficos (CWE-327, 328, 330, 321, 295, 916)
- MD5/SHA-1 para integridad o contraseñas, DES/3DES, ECB, IV/nonce fijo o reutilizado.
- PRNG no criptográfico para tokens, OTP, IDs de sesión (`Random`, `math/rand`, `Math.random`).
- Llaves embebidas; contraseñas sin hash adaptativo (bcrypt, scrypt, Argon2id, PBKDF2).
- Verificación TLS deshabilitada; comparación de MAC/tokens no constante en tiempo.

### A05 Inyección (CWE-89, 943, 78, 77, 90, 611, 917, 79, 1336)
- SQL/NoSQL por concatenación o formato; identificadores dinámicos sin lista blanca.
- Comandos de sistema con entrada; LDAP; XXE; SpEL/OGNL/plantillas con entrada (SSTI).
- XSS: sinks de DOM sin codificar, bypass de sanitizador del framework.
- Salida de LLM usada en SQL, shell, `eval` o HTML (ver LLM05).

### A06 Diseño inseguro (CWE-840, 841, 799)
- Flujos de negocio sin límite o sin idempotencia (transferencias, OTP, cupones).
- Falta de separación de funciones/aprobación dual donde la regla de negocio la exige.
- Estados que pueden saltarse (aprobar sin validar), carreras en saldo/cupo (TOCTOU).

### A07 Fallos de autenticación (CWE-287, 307, 384, 613, 347, 798)
- JWT: firma no verificada, `alg` controlable, sin validar `iss`/`aud`/`exp`/`nbf`,
  llave HMAC débil, aceptar tokens de otro tenant/app.
- OAuth/OIDC: `redirect_uri` laxo, falta de `state`/PKCE, implicit flow, tokens en URL.
- Fuerza bruta sin bloqueo/limitación en login u OTP; fijación de sesión; logout sin invalidar.

### A08 Fallos de integridad de software o datos (CWE-502, 345, 353)
- Deserialización de tipos arbitrarios (Java nativo, Jackson default typing, YAML inseguro).
- Webhooks sin verificar firma; artefactos/actualizaciones sin verificación de integridad.
- Caches o colas que aceptan mensajes sin autenticar el productor.

### A09 Fallos de registro y alertas (CWE-778, 532, 117)
- Eventos de seguridad sin auditoría (login fallido, cambio de permisos, acceso denegado).
- PII, PAN, tokens o contraseñas en logs, trazas, métricas o eventos.
- Log injection (CRLF) con entrada sin neutralizar.

### A10 Manejo indebido de condiciones excepcionales (CWE-755, 754, 636, 209)
- Fallar abierto: excepción en la verificación → se permite el acceso.
- `catch` que traga errores de autorización o de firma y continúa.
- Recursos no liberados en la ruta de error; estados parciales sin compensación.

## 2. OWASP API Security Top 10:2023

| ID | Riesgo | Señal en código |
|---|---|---|
| API1 | Broken Object Level Authorization | ID de objeto del request sin verificación de pertenencia |
| API2 | Broken Authentication | Validación de token incompleta, credenciales en query, endpoints de auth sin límite |
| API3 | Broken Object Property Level Authorization | Respuesta con la entidad completa; DTO de entrada que acepta campos privilegiados |
| API4 | Unrestricted Resource Consumption | Paginación sin tope, payload/archivo sin límite, consultas costosas sin rate limit |
| API5 | Broken Function Level Authorization | Operaciones admin accesibles con rol de usuario; verbos HTTP no cubiertos |
| API6 | Unrestricted Access to Sensitive Business Flows | Flujos automatizables (OTP, registro, transferencias) sin anti-automatización |
| API7 | Server Side Request Forgery | Cliente HTTP con URL/host derivado de entrada |
| API8 | Security Misconfiguration | CORS, TLS, cabeceras, verbos, errores verbosos |
| API9 | Improper Inventory Management | Versiones viejas o endpoints de prueba expuestos, ausentes del catálogo `14.00` |
| API10 | Unsafe Consumption of APIs | Confiar en respuestas de terceros sin validar esquema, tamaño, redirecciones |

Cruza con `14.00` de archi: un endpoint en código que no está en el catálogo es API9.

## 3. LLM y Agentic

LLM 2025: LLM01 Prompt Injection · LLM02 Sensitive Information Disclosure · LLM03
Supply Chain · LLM04 Data and Model Poisoning · LLM05 Improper Output Handling · LLM06
Excessive Agency · LLM07 System Prompt Leakage · LLM08 Vector and Embedding Weaknesses ·
LLM09 Misinformation · LLM10 Unbounded Consumption.

Agentic 2026: `ASI01`–`ASI10` (Goal Hijack, Tool Misuse, Identity and Privilege Abuse,
Agentic Supply Chain, Unexpected Code Execution, Memory and Context Poisoning, Insecure
Inter-Agent Communication, Cascading Failures, Human-Agent Trust Exploitation, Rogue
Agents). Detalle de verificación en [IA, agentes y MCP](ia-agentes-mcp.md).

## 4. CWE frecuentes y su sumidero típico

| CWE | Sumidero típico |
|---|---|
| 89 SQLi | `Statement.execute`, `createNativeQuery(String concat)`, `DatabaseClient.sql(concat)`, `db.Query(fmt.Sprintf…)` |
| 78 OS command | `Runtime.exec`, `ProcessBuilder` con shell, `exec.Command("sh","-c",…)` |
| 22 Path traversal | `Paths.get(base, input)` sin normalizar/validar prefijo, `filepath.Join` sin `filepath.IsLocal`/raíz confinada |
| 918 SSRF | `WebClient`/`RestTemplate`/`http.Get` con URL de entrada |
| 79 XSS | `innerHTML`, `bypassSecurityTrust*`, `[innerHTML]` con contenido no sanitizado, `template.HTML(input)` |
| 502 Deserialización | `ObjectInputStream`, `enableDefaultTyping`/`activateDefaultTyping` amplio, `SnakeYAML` sin `SafeConstructor` |
| 611 XXE | `DocumentBuilderFactory` sin deshabilitar DTD/entidades externas |
| 295 TLS | `TrustAllCerts`, `InsecureTrustManagerFactory`, `InsecureSkipVerify: true` |
| 330 PRNG | `java.util.Random`, `math/rand`, `Math.random()` para secretos |
| 532 Log de sensibles | `log.info("{}", request)`, `@ToString`/`@Data` en entidades con PII |
| 639 IDOR | Repositorio `findById(idDelRequest)` sin filtro por dueño |
| 798 Credenciales embebidas | Literales en código, YAML, `.properties`, Dockerfile, HCL, tests |
| 1333 ReDoS | Regex con cuantificadores anidados sobre entrada sin límite |
