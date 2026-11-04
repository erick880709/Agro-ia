# Perfil de seguridad Angular

Complementa los perfiles Angular de builder (`angular-routing-http-forms.md`,
`angular-review-and-debugging.md`). Recuerda la frontera: **todo control en el navegador
es usabilidad, no seguridad**. Un guard, un `*ngIf` por rol o un botón oculto sin el
control equivalente en el backend es hallazgo del backend (BFLA/BOLA), no del frontend.

## Tabla de contenido

1. XSS y sanitización
2. Tokens, sesión y OIDC
3. HTTP e interceptores
4. Configuración, build y dependencias
5. CSP y cabeceras
6. Datos en el cliente

## 1. XSS y sanitización

- Angular escapa interpolaciones y sanitiza `[innerHTML]`, `[src]`, `[href]`, `[style]`.
  Los riesgos aparecen al saltarlo:
  - `DomSanitizer.bypassSecurityTrustHtml|Url|ResourceUrl|Script|Style` con datos de
    usuario o de API → XSS (CWE-79). Exige sanitización previa explícita
    (`DOMPurify`) o eliminar el bypass.
  - Acceso directo al DOM: `ElementRef.nativeElement.innerHTML`, `Renderer2.setProperty(el,
    'innerHTML', x)`, `document.write`, `insertAdjacentHTML`.
  - `[href]` con `javascript:` cuando el valor se construye fuera del sanitizador.
- Plantillas generadas dinámicamente con contenido de usuario (compilación en runtime):
  inyección de plantillas.
- Contenido generado por LLM renderizado como HTML/Markdown: trátalo como entrada no
  confiable (LLM05) y sanitiza el HTML resultante del Markdown.

## 2. Tokens, sesión y OIDC

- Preferido: cookies `HttpOnly; Secure; SameSite` gestionadas por backend (BFF) o tokens
  en memoria con librería OIDC (`angular-auth-oidc-client`, MSAL Angular). Tokens de
  acceso/refresh en `localStorage`/`sessionStorage` amplían el impacto de cualquier XSS:
  hallazgo `medium` solo si hay XSS o dependencia comprometible trazada; si no, nota de
  hardening con la decisión del proyecto.
- Authorization Code + PKCE; implicit flow es obsoleto (hallazgo).
- `redirectUri`/`postLogoutRedirectUri` construidos desde la URL actual sin lista blanca.
- Logout que no invalida sesión en el IdP/backend.

## 3. HTTP e interceptores

- Interceptor que añade el bearer token a **cualquier** URL: fuga del token a terceros.
  Debe comparar el **origen** contra una lista de APIs propias (no `startsWith` de la
  URL, que acepta `https://api.banco.com.attacker.io`).
- `withCredentials: true` hacia orígenes externos.
- Protección XSRF: `HttpClientXsrfModule`/`withXsrfConfiguration` cuando la auth es por
  cookie; Angular no envía el header en peticiones absolutas a otros orígenes.
- Manejo de errores que muestra en pantalla el cuerpo del error del backend sin filtrar.

## 4. Configuración, build y dependencias

- `environment*.ts` con API keys, client secrets o connection strings: todo lo que va al
  bundle es público. Un *client secret* OAuth en un SPA es hallazgo (cliente público ≠
  confidencial).
- Source maps publicados en producción (`sourceMap: true` en configuración prod) →
  divulgación de código; nota de hardening salvo que expongan secretos o lógica sensible.
- `npm audit --omit=dev` / OSV-Scanner sobre `package-lock.json`; scripts `postinstall`
  de dependencias nuevas; versiones de Angular fuera de soporte (sin parches de seguridad).

## 5. CSP y cabeceras

- Angular soporta CSP estricta con `ngCspNonce`/`CSP_NONCE` (16+) e `autoCsp`
  (versiones recientes; verifica la instalada). `unsafe-inline` en `script-src` anula la
  mitigación de XSS.
- Trusted Types: Angular es compatible; recomiéndalo en apps de banca cuando el
  servidor/CDN lo permite.
- Cabeceras (servidor/CDN): `Content-Security-Policy`, `X-Content-Type-Options`,
  `Referrer-Policy`, `frame-ancestors`/`X-Frame-Options` para clickjacking en
  operaciones sensibles.

## 6. Datos en el cliente

- PII o datos financieros en `localStorage`, IndexedDB o service worker cache sin
  necesidad; caché de respuestas sensibles en el SW (`ngsw-config.json` `dataGroups`).
- Logs de consola (`console.log`) con tokens o datos de cliente en builds productivos.
- Telemetría/analítica que envía URLs con identificadores o tokens en query string.
