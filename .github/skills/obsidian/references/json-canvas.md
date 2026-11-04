# JSON Canvas

Referencia de la especificación **JSON Canvas 1.0** (https://jsoncanvas.org/spec/1.0/) para crear y
editar `.canvas`. Fuente: `kepano/obsidian-skills` (`json-canvas`).

## Estructura de archivo

Un `.canvas` contiene dos arrays de primer nivel:

```json
{
  "nodes": [],
  "edges": []
}
```

## Nodos

Objetos colocados en el lienzo. El orden del array define el z-index: el primero queda abajo,
el último arriba.

### Atributos comunes

| Atributo | Requerido | Tipo | Descripción |
|---|---|---|---|
| `id` | sí | string | Identificador único de 16 caracteres hex |
| `type` | sí | string | `text`, `file`, `link` o `group` |
| `x` | sí | integer | Posición X en píxeles (arriba-izquierda) |
| `y` | sí | integer | Posición Y en píxeles |
| `width` | sí | integer | Ancho en píxeles |
| `height` | sí | integer | Alto en píxeles |
| `color` | no | canvasColor | Preset `"1"`–`"6"` o hex (`"#FF0000"`) |

### Nodo de texto

```json
{
  "id": "6f0ad84f44ce9c17",
  "type": "text",
  "x": 0, "y": 0, "width": 400, "height": 200,
  "text": "# Hola\n\nContenido **Markdown**."
}
```

Trampa de saltos de línea: usa `\n` real en el JSON; no el literal `\\n` (Obsidian mostraría los
caracteres `\` y `n`).

### Nodo de archivo

```json
{
  "id": "a1b2c3d4e5f67890",
  "type": "file",
  "x": 500, "y": 0, "width": 400, "height": 300,
  "file": "Adjuntos/diagrama.png",
  "subpath": "#Encabezado"
}
```

- `file`: ruta relativa a la raíz del vault.
- `subpath` (opcional): enlace a encabezado o bloque (empieza con `#`).

### Nodo de enlace

```json
{
  "id": "c3d4e5f678901234",
  "type": "link",
  "x": 1000, "y": 0, "width": 400, "height": 200,
  "url": "https://obsidian.md"
}
```

### Nodo de grupo

```json
{
  "id": "d4e5f6789012345a",
  "type": "group",
  "x": -50, "y": -50, "width": 1000, "height": 600,
  "label": "Resumen del proyecto",
  "color": "4"
}
```

Opcionales: `background` (ruta a imagen), `backgroundStyle` (`cover`, `ratio`, `repeat`).

## Aristas

Conectan nodos con `fromNode` y `toNode`.

| Atributo | Requerido | Tipo | Defecto | Descripción |
|---|---|---|---|---|
| `id` | sí | string | — | Identificador único |
| `fromNode` | sí | string | — | Id del nodo origen |
| `fromSide` | no | string | — | `top`, `right`, `bottom`, `left` |
| `fromEnd` | no | string | `none` | `none` o `arrow` |
| `toNode` | sí | string | — | Id del nodo destino |
| `toSide` | no | string | — | `top`, `right`, `bottom`, `left` |
| `toEnd` | no | string | `arrow` | `none` o `arrow` |
| `color` | no | canvasColor | — | Color de la línea |
| `label` | no | string | — | Texto de la arista |

```json
{
  "id": "0123456789abcdef",
  "fromNode": "6f0ad84f44ce9c17",
  "fromSide": "right",
  "toNode": "a1b2c3d4e5f67890",
  "toSide": "left",
  "toEnd": "arrow",
  "label": "conduce a"
}
```

## Colores

`canvasColor` acepta un preset numérico o hex:

| Preset | Color |
|---|---|
| `"1"` | Rojo |
| `"2"` | Naranja |
| `"3"` | Amarillo |
| `"4"` | Verde |
| `"5"` | Cian |
| `"6"` | Púrpura |

## Generación de ids

16 caracteres hexadecimales en minúscula (valor aleatorio de 64 bits), p. ej. `6f0ad84f44ce9c17`.

## Pautas de layout

- Las coordenadas pueden ser negativas (el lienzo es infinito).
- `x` crece a la derecha, `y` hacia abajo; la posición es la esquina superior izquierda.
- Separa nodos 50–100 px; deja 20–50 px de padding dentro de grupos.
- Alinea a la cuadrícula (múltiplos de 10 o 20).

| Tipo de nodo | Ancho sugerido | Alto sugerido |
|---|---|---|
| Texto pequeño | 200–300 | 80–150 |
| Texto medio | 300–450 | 150–300 |
| Texto grande | 400–600 | 300–500 |
| Vista de archivo | 300–500 | 200–400 |
| Vista de enlace | 250–400 | 100–200 |

## Lista de validación

1. Todos los `id` son únicos entre nodos y aristas.
2. Cada `fromNode` y `toNode` referencia un nodo existente.
3. Campos requeridos presentes por tipo (`text` en texto, `file` en archivo, `url` en enlace).
4. `type` ∈ {`text`, `file`, `link`, `group`}.
5. `fromSide`/`toSide` ∈ {`top`, `right`, `bottom`, `left`}.
6. `fromEnd`/`toEnd` ∈ {`none`, `arrow`}.
7. Colores preset `"1"`–`"6"` o hex válido.
8. JSON válido y parseable.

La skill automatiza esta lista con `obsidian.mjs validate-canvas <archivo.canvas>`.
