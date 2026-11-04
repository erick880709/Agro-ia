# Guía: Diagramas Excalidraw en archi

Excalidraw es el formato de archi para **diagramas explicativos y conceptuales**: argumentos
para el Comité, mapas de contexto, explicaciones de una decisión, deltas AS-IS → TO-BE
narrados, onboarding. Basada en `excalidraw-diagram-skill` (coleam00) y en las reglas de
`references/guia-calidad-visual-diagramas.md`, que siguen aplicando.

Lee antes `references/guia-diseno-diagramas.md` (qué dibujar y para quién).

## Contenido

1. Cuándo usar Excalidraw (y cuándo no)
2. Nombre, ubicación y trazabilidad
3. Método de diseño
4. Patrones visuales
5. Paleta semántica de archi
6. Reglas técnicas del JSON
7. Plantillas de elementos
8. Construcción por secciones
9. Validación y vista previa
10. Con MCP de Excalidraw

## 1. Cuándo usar Excalidraw (y cuándo no)

| Usar Excalidraw | No usar Excalidraw |
|---|---|
| Explicar **por qué** (decisión, trade-off, argumento) con formas que significan | Diagramas dueños que deben compilar en Markdown (`09`, `14`, `15`, `16.xx`): son Mermaid |
| Mapa de contextos/bounded contexts y relaciones de equipo | Despliegue con iconos oficiales (`17.1`–`17.3`): es `.drawio` |
| Delta AS-IS → TO-BE narrado para el Comité | Un flujo que se recorre paso a paso: es el HTML interactivo |
| Diagrama técnico con evidencia (payloads, eventos reales) que no cabe en Mermaid | Algo que una tabla o un párrafo explican igual |

## 2. Nombre, ubicación y trazabilidad

- Archivo: `<NN>.<k>-<Tema>_<Proyecto>.excalidraw` con el número del **artefacto dueño** y un
  consecutivo estable (p. ej. `10.2-Argumento-Seleccion_<Proyecto>.excalidraw`,
  `23.1-Delta-AS-IS-TO-BE_<Proyecto>.excalidraw`). Exportación opcional con el mismo nombre
  `.png`/`.svg`.
- El artefacto dueño lo enlaza y explica en 1–3 frases lo que el diagrama no muestra.
- Los elementos que representan algo del modelo llevan su ID estable en el texto
  (`CT-03 API de Pagos`, `EXT-02 PSE`, `DATA-007`, `TB-01`) y, cuando el MCP o la app lo
  permitan, en `customData.archiId`. El validador cruza esos IDs con el dueño si se le indica.
- Nada que no exista en el artefacto dueño aparece en el diagrama.

## 3. Método de diseño

1. **Profundidad.** ¿Conceptual (abstracto) o técnico (con evidencia)? En técnico, obtén los
   nombres reales de `14.00`, `15`, `16.xx`, `19.1` antes de dibujar.
2. **Entender qué HACE cada concepto** (no qué es) y qué relación tiene con los demás.
3. **Mapear concepto → patrón** (§4). Cada concepto principal usa un patrón distinto; nada de
   rejillas de tarjetas iguales.
4. **Trazar el recorrido del ojo**: izquierda → derecha o arriba → abajo para secuencias; radial
   para hub-and-spoke. Debe haber una historia visual.
5. **Generar el JSON por secciones** (§8).
6. **Validar y mirar** (§9) hasta que no queden defectos.

## 4. Patrones visuales

| Si el concepto… | Patrón | Forma |
|---|---|---|
| Genera varias salidas | Abanico | Un nodo, flechas radiales |
| Combina entradas | Convergencia | Flechas que confluyen en un nodo |
| Tiene jerarquía | Árbol | Líneas + texto libre, sin cajas |
| Es una secuencia | Línea de tiempo | Línea + puntos (10–20 px) + etiquetas |
| Se repite/mejora | Ciclo | Flecha que vuelve al inicio |
| Transforma algo | Línea de ensamblaje | Antes → proceso → después, con muestras reales |
| Compara dos cosas | Lado a lado | Dos estructuras paralelas con contraste |
| Separa fases o zonas | Corte/frontera | Espacio o `frame` rotulado |
| Es un contexto abstracto | Nube | Elipses superpuestas |

Reglas de forma: rectángulo = proceso/componente; elipse = inicio/fin/externo; rombo =
decisión; cilindro simulado (elipse + rectángulo) solo si el dato es protagonista; texto libre
para títulos, descripciones y metadatos. **Menos del 30 % del texto dentro de contenedores.**

## 5. Paleta semántica de archi

Misma semántica que las clases Mermaid de la guía de calidad visual. No inventes colores.

| Rol | Relleno | Borde | Trazo |
|---|---|---|---|
| Neutro / componente | `#FFFFFF` | `#42526E` | continuo |
| Foco (máx. 2) | `#FFF4E5` | `#C25100` | continuo, `strokeWidth` 2 |
| Datos / almacenamiento | `#E9F2FF` | `#0C66E4` | continuo |
| Externo | `#FFFFFF` | `#6B778C` | discontinuo |
| Nuevo (TO-BE) | `#DCFFF1` | `#1F845A` | continuo |
| Retirado (AS-IS) | `#FFECEB` | `#AE2E24` | discontinuo |
| Modificado | `#FFF7D6` | `#946F00` | continuo |
| Frontera de confianza / zona | `transparent` | `#6B778C` | discontinuo (`frame` o rectángulo) |
| Evidencia (código/payload) | `#1E293B` | `#1E293B` | texto `#E2E8F0`, monoespaciado |

Texto: títulos `#172B4D` (24–28 px), subtítulos `#42526E` (18–20 px), detalle `#626F86`
(14–16 px). Fondo del lienzo `#FFFFFF`.

## 6. Reglas técnicas del JSON

- Raíz: `{"type":"excalidraw","version":2,"source":"archi","elements":[…],"appState":{"viewBackgroundColor":"#FFFFFF","gridSize":20},"files":{}}`.
- `id` descriptivos y únicos (`ct03_rect`, `arr_ct03_data007`); `seed` por sección (100xxx,
  200xxx…).
- `roughness: 0` y `opacity: 100` en entregables formales (`roughness: 1` solo en bocetos
  marcados como tales). `fontFamily: 2` (sans) para etiquetas y `3` (monoespaciada) para
  código, puertos y evidencia; evita las tipografías manuscritas en entregables al Comité.
- **Conectores ortogonales**: usa flechas en codo (`"elbowed": true`) o `points` con tramos
  solo horizontales/verticales; nunca diagonales (regla de la guía de calidad visual).
- **Vinculación bidireccional**: la flecha declara `startBinding`/`endBinding`
  (`{"elementId": "...", "focus": 0, "gap": 6}`) y cada forma enlazada lista la flecha en
  `boundElements` (`{"id": "...", "type": "arrow"}`). Texto dentro de una forma: el texto
  lleva `containerId` y la forma lo lista en `boundElements` (`type: "text"`).
- `text` y `originalText` solo con palabras legibles; saltos con `\n`.
- Etiquetas de conectores: verbo + protocolo, ≤ 40 caracteres, como texto vinculado a la
  flecha o texto libre junto al tramo, sin tocar la línea.
- Zonas con `type: "frame"` (`name` = título) o rectángulo discontinuo; ningún nodo se sale de
  su zona.
- Leyenda: franja inferior con un ejemplo por rol usado.
- Presupuesto: el de la guía de calidad visual para el tipo equivalente; para explicativos
  libres, ≤ 15 formas protagonistas y ≤ 20 conectores; si se excede, vista general + detalle.

## 7. Plantillas de elementos

Rectángulo con texto vinculado (completa colores desde §5):

```json
{"type":"rectangle","id":"ct03_rect","x":400,"y":200,"width":220,"height":90,
 "strokeColor":"#42526E","backgroundColor":"#FFFFFF","fillStyle":"solid","strokeWidth":2,
 "strokeStyle":"solid","roughness":0,"opacity":100,"angle":0,"seed":100001,"version":1,
 "versionNonce":100002,"isDeleted":false,"groupIds":[],"frameId":null,"link":null,"locked":false,
 "roundness":{"type":3},"boundElements":[{"id":"ct03_text","type":"text"},{"id":"arr_ct03_db","type":"arrow"}],
 "customData":{"archiId":"CT-03"}},
{"type":"text","id":"ct03_text","x":410,"y":222,"width":200,"height":46,
 "text":"CT-03 API de Pagos\nJava 21 · Spring WebFlux","originalText":"CT-03 API de Pagos\nJava 21 · Spring WebFlux",
 "fontSize":16,"fontFamily":2,"textAlign":"center","verticalAlign":"middle","lineHeight":1.25,
 "strokeColor":"#172B4D","backgroundColor":"transparent","fillStyle":"solid","strokeWidth":1,
 "strokeStyle":"solid","roughness":0,"opacity":100,"angle":0,"seed":100003,"version":1,
 "versionNonce":100004,"isDeleted":false,"groupIds":[],"frameId":null,"link":null,"locked":false,
 "boundElements":null,"containerId":"ct03_rect"}
```

Flecha en codo vinculada:

```json
{"type":"arrow","id":"arr_ct03_db","x":620,"y":245,"width":160,"height":0,
 "points":[[0,0],[160,0]],"elbowed":true,
 "startBinding":{"elementId":"ct03_rect","focus":0,"gap":6},
 "endBinding":{"elementId":"data007_rect","focus":0,"gap":6},
 "startArrowhead":null,"endArrowhead":"arrow",
 "strokeColor":"#42526E","backgroundColor":"transparent","fillStyle":"solid","strokeWidth":2,
 "strokeStyle":"solid","roughness":0,"opacity":100,"angle":0,"seed":100005,"version":1,
 "versionNonce":100006,"isDeleted":false,"groupIds":[],"frameId":null,"link":null,"locked":false,
 "boundElements":[]}
```

Bloque de evidencia (payload real de `14.xx.y`): rectángulo `#1E293B` + texto `fontFamily: 3`,
`fontSize: 13–14`, color `#E2E8F0`, sin `containerId` si el texto es largo (texto libre
superpuesto y alineado dentro del rectángulo).

## 8. Construcción por secciones

En diagramas completos **no generes todo el JSON de una vez**:

1. Crea el archivo con la raíz y la primera sección (entrada/disparador).
2. Agrega una sección por edición (zona, decisión, sección protagonista, salidas), con IDs y
   semillas por sección.
3. Actualiza las vinculaciones entre secciones en ambos extremos a medida que avanzas.
4. Revisa el conjunto: IDs y vinculaciones existentes, espaciado equilibrado.
5. Valida y mira (§9).

## 9. Validación y vista previa

```bash
python scripts/validate_excalidraw.py <archivo>.excalidraw --strict [--owner <artefacto-dueño>.md]
python scripts/render_preview.py <archivo>.excalidraw -o /tmp/<archivo>.png
```

`validate_excalidraw.py` verifica JSON, IDs únicos, vinculaciones bidireccionales y existentes,
texto contenido, conectores ortogonales, `roughness`/`opacity`, colores de la paleta,
solapamientos de formas, desborde aproximado de texto, leyenda, presupuesto, proporción de
texto en contenedores y, con `--owner`, que cada ID de archi del diagrama exista en el dueño.
`--inventory` imprime nodos y relaciones para importar o comparar.

`render_preview.py` dibuja una vista previa aproximada (formas, textos, flechas) para que
puedas **mirar** el resultado y aplicar el bucle de `guia-diseno-diagramas.md` §9. No sustituye
el render real de Excalidraw: si el MCP o la app permiten exportar, revisa también ese PNG.

## 10. Con MCP de Excalidraw

Si `excalidraw-remoto` está disponible (ver `references/guia-mcp-diagramacion.md`):

- Define primero el plan (§3) y los IDs desde los artefactos dueños; el MCP es un medio de
  edición, no una fuente de decisiones.
- Pide o construye la escena por secciones; aplica la paleta de §5 y las reglas de §6.
- Exporta el JSON resultante a `<NN>.<k>-…excalidraw`, valídalo y míralo como cualquier otro.
- Registra en el artefacto dueño que fue asistido por MCP, con fecha y resultado de validación.
