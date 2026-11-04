# Capabilities y overlays

## Capability

Usa una capability para una característica reusable que pueda componerse sobre una familia base: autenticación, OTP, websocket, i18n, cliente tipado, persistencia o integración transversal.

Debe declarar:

- Identidad y versión.
- Familias/runtimes compatibles.
- Dependencias, orden e incompatibilidades.
- Inputs y defaults seguros.
- Archivos o zonas administradas.
- Transformación y migraciones.
- Validaciones y permisos requeridos.

Resuelve el grafo de capabilities antes de renderizar. Rechaza ciclos y combinaciones incompatibles. Aplica orden topológico estable para preservar determinismo.

## Capability `design-system`

Compone un sistema de diseño congelado sobre una familia `web` o `library` sin fijar ninguna marca en la plantilla:

- **Inputs:** tokens del proyecto (`*.tokens.json`, W3C Design Tokens), catálogo de componentes, manifiesto de assets de marca y, si existe, paquete compartido con versión exacta. Los defaults del arquetipo son neutrales (tema base del UI kit), nunca la marca de una solución concreta.
- **Transformación:** tema y variables CSS generados desde los tokens por un paso determinista; componentes compartidos consumidos desde el paquete o la zona declarada, no copiados por feature; assets referenciados desde el manifiesto, nunca redibujados.
- **Zonas administradas:** solo la zona de estilos declarada (`style_zones`) puede contener literales de color o tipografía.
- **Validaciones:** `check-design-conformance`, gates `design-conformance`/`a11y` del adaptador cuando existan, y dos golden projects con paquetes de tokens distintos que pasan los mismos gates sin cambiar código.
- **Incompatibilidades:** estilos globales o temas paralelos que redefinen los mismos tokens fuera de la zona declarada.

Un overlay de marca por solución (otro paquete de tokens y assets) es válido; un fork del arquetipo para cambiar colores no lo es.

## Overlay

Usa overlay para adaptar una instancia sin modificar la fuente del arquetipo. Debe vivir con la solución o en un catálogo separado y declarar:

- Motivo y fuente arquitectónica.
- Arquetipo/capability objetivo y rango compatible.
- Archivos o puntos de extensión afectados.
- Orden de aplicación.
- Ownership resultante.
- Validaciones y estrategia de upgrade.

No uses overlay para ocultar una divergencia estructural permanente. Si varios proyectos repiten el mismo overlay, evalúa convertirlo en capability. Si cambia la estructura esencial, evalúa otra familia.

## Evitar explosión combinatoria

No crees familias como `react-auth-i18n-otp-websocket`. Prefiere `react-vite-spa` más capabilities independientes. Crea otra familia solo cuando cambie el modelo de ejecución, el patrón estructural o un atributo no componible de forma segura.

