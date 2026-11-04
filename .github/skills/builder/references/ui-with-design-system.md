# UI con sistema de diseño

Aplica esta guía cuando el cambio toca interfaz de usuario y el proyecto declara un
sistema de diseño: tokens (`*.tokens.json`), catálogo de componentes, manifiesto de
assets de marca, paquete o tema compartido, o una capability `design-system` en su
blueprint/receipt. Si no existe ninguno, sigue los patrones visuales del módulo de
referencia y registra la ausencia como observación; no crees un sistema de diseño
como parte de una feature.

## Fuentes antes de tocar la UI

| Necesidad | Fuente |
|---|---|
| Qué hace la pantalla, acciones, estados y edge cases | Especificación de pantalla del proyecto (p. ej. `SCR-*`) |
| Qué componente usar, variantes y estado de implementación | Catálogo de componentes (`CMP-*`) y su sección `Implementation` |
| Colores, tipografía, radios, espaciado, elevación | Tokens del proyecto, a través del tema o paquete que los materializa |
| Logos, favicon, ilustraciones e íconos de marca | Manifiesto de assets de marca |
| Estructura de página | Plantillas y patrones de página del sistema de diseño |

Lee la fuente real; un nombre de carpeta o un componente parecido en otra feature no
sustituye el catálogo.

## Reglas

1. Compón con los componentes y patrones existentes. Configúralos por sus props; no
   los envuelvas para cambiarles colores, tamaños o bordes.
2. No escribas literales de color (hex, `rgb()`, `hsl()`) ni tamaños tipográficos en
   px fuera de la zona de estilos que el proyecto declara. Usa tokens o props.
3. No dupliques dentro de una feature un componente que ya existe en el catálogo o en
   la capa compartida. Si la regla de boundaries impide importarlo, el componente
   pertenece a la capa compartida: repórtalo, no lo copies.
4. No redibujes ni aproximes logos, ilustraciones o íconos de marca. Usa los assets
   del manifiesto; si falta uno, usa el placeholder que el manifiesto indique.
5. Si falta un componente, variante, token o asset, no lo inventes. Registra un
   `design-system-gap` con: pantalla y componente afectados, necesidad concreta,
   alternativa temporal usada (la pieza existente más cercana, sin estilizarla
   localmente) y dueño (UX / sistema de diseño). Refléjalo en la especificación del
   cambio para que no se pierda.
6. Cambiar el sistema de diseño (nuevo token, variante o componente compartido) es un
   encargo con su propio dueño. No lo incluyas dentro de una feature salvo mandato
   explícito que lo autorice.

## Validación

- Ejecuta los gates de diseño que declare el proyecto: lint de estilos, pruebas de
  arquitectura sobre literales, `check-design-conformance` de `solution-baseline`
  cuando exista baseline, y pruebas de accesibilidad automatizadas.
- Cuando la presentación importe, verifica visualmente la pantalla contra su
  wireframe y sus estados en los tamaños de viewport que declare el proyecto.
- En la evidencia del cambio, lista los componentes y tokens usados y cualquier
  `design-system-gap` abierto. Un gap abierto no impide cerrar la feature si la
  alternativa temporal quedó registrada; sí impide declarar conformidad visual.
