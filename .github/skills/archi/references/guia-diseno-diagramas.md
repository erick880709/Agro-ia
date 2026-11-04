# Guía: Diseño de diagramas explicativos

Esta guía es el **método** previo a dibujar: decide qué diagrama hacer, para quién, con qué
herramienta y cómo comprobar que explica. Las **reglas visuales** (notación, conectores,
presupuesto, composición `.drawio`) siguen siendo dueñas de
`references/guia-calidad-visual-diagramas.md`; las herramientas tienen su guía propia:
`references/guia-excalidraw.md` y `references/guia-diagramas-interactivos.md`.

Basada en `diagram-design` (cathrynlavery y Microsoft devsquad), `excalidraw-diagram-skill`
(coleam00), `architecture-diagram-skill` (konraddzbik) y Archify (tt-a1i), adaptada al
gobierno de archi (IDs estables, artefactos dueños, validadores, Comité de Arquitectura).

## Contenido

1. Principio: un diagrama argumenta
2. Las cinco decisiones antes de dibujar
3. Enrutador: pregunta → patrón → tipo → herramienta
4. Multi-zoom: resumen, límites, detalle
5. Evidencia concreta
6. Audiencia y diales de salida
7. Diagramas de cambio (AS-IS → TO-BE)
8. Accesibilidad
9. Bucle renderizar → mirar → corregir
10. Importar diagramas existentes
11. Exportar y publicar
12. Checklist de explicación

## 1. Principio: un diagrama argumenta

Un diagrama no es texto con cajas: es un argumento visual. Dos pruebas antes de cerrarlo:

- **Prueba de isomorfismo.** Si se borra todo el texto, ¿la forma sigue comunicando la idea?
  Un *fan-out* debe verse como abanico, una convergencia como embudo, un ciclo como ciclo,
  una frontera de confianza como contenedor. Cinco cajas iguales en fila no argumentan nada.
- **Prueba de aprendizaje.** ¿Alguien aprende algo concreto (un protocolo, un payload, un
  puerto, un orden de pasos, una decisión) que no estaba claro en el párrafo? Si un párrafo o
  una tabla de tres columnas comunica lo mismo, no dibujes.

La jugada de mayor calidad suele ser **quitar**: dos nodos que siempre viajan juntos son uno;
una flecha obvia por contención sobra; una etiqueta que repite el nombre del nodo se reduce.
La prueba de eliminación de la guía de calidad visual sigue aplicando.

## 2. Las cinco decisiones antes de dibujar

Declara el plan en una línea por diagrama (la guía de calidad visual lo exige):

| Decisión | Pregunta | Ejemplo |
|---|---|---|
| Pregunta | ¿Qué responde este diagrama? | "¿Qué cruza la frontera de confianza al pagar?" |
| Audiencia | `ingenieria`, `mixta` o `ejecutiva` (§6) | Comité = `mixta` |
| Patrón semántico | ¿Qué comportamiento carga el significado? (§3) | Camino pavimentado seguro |
| Tipo y herramienta | ¿Qué tipo y en qué formato? (§3) | C4 L2 Mermaid + flujo interactivo |
| Recortes | ¿Qué se divide por presupuesto y a qué vista va? | Integraciones a `14.xx` |

## 3. Enrutador: pregunta → patrón → tipo → herramienta

Primero el **patrón semántico** (qué comportamiento explica), luego el **tipo** (gramática de
layout), al final la **herramienta**. Un patrón no añade una segunda gramática de layout.

| Si la pregunta trata de… | Patrón semántico | Tipo | Artefacto dueño | Herramienta por defecto |
|---|---|---|---|---|
| Qué es el sistema y con quién habla | Contexto | C4 L1 | `14` | Mermaid `C4Context` |
| Qué se despliega por separado y cómo se comunica | Contenedores | C4 L2 | `14` | Mermaid `C4Container` |
| Cómo está hecho un contenedor | Componentes | C4 L3 | `14.xx` | Mermaid |
| Qué pasa, en orden, en un flujo crítico | Secuencia con ruta de error | Secuencia | `15` | Mermaid `sequenceDiagram` |
| Cómo viaja una petición o un dato paso a paso, para recorrerlo | Recorrido de flujo | Flujo interactivo | `15.1` | HTML interactivo (§ `guia-diagramas-interactivos.md`) |
| Dónde corre, en qué red y nube | Despliegue por zonas | Despliegue | `17.1`–`17.3`, `17.6.N` | `.drawio` con iconos curados |
| Qué está permitido y prohibido cruzar entre zonas | Camino pavimentado seguro | Arquitectura con fronteras | `19.1`, `17.6` | Mermaid `subgraph TB-xx` o `.drawio` |
| Qué controles se aplican en qué capa | Catálogo de controles por capa | Pila de capas | `19.1`, `18` | Mermaid o Excalidraw |
| Cómo progresa una entidad por estados, reintentos y finales | Ciclo de vida | Máquina de estados | `16.xx`, `18` | Mermaid `stateDiagram-v2` |
| Qué entidades, claves y cardinalidades | Modelo de datos | ER | `16.xx` | Mermaid `erDiagram` |
| Qué opciones se comparan y en qué difieren estructuralmente | Lado a lado | Alternativas | `09` | Mermaid por alternativa |
| Qué cambia entre hoy y el objetivo | Delta de arquitectura (§7) | Antes/después + bitácora | `23`, `24` | Mermaid pareado o interactivo con modos |
| Qué hacer y en qué orden de transición | Hoja de ruta | Línea de tiempo/Gantt | `24` | Mermaid `gantt`/`timeline` |
| Un concepto o argumento para el comité (por qué esta decisión) | Argumento visual (abanico, convergencia, embudo, ciclo) | Explicativo libre | `09`, `10`, `20`, `25.1` | Excalidraw |
| Dominios, bounded contexts y relaciones de equipo | Mapa de contextos | Mapa | `10.1`, `14` | Excalidraw o Mermaid |
| Uno a muchos / muchos a uno / transformación | Abanico, convergencia, línea de ensamblaje | Flujo de datos | `14.xx`, `16` | Excalidraw o Mermaid |

Reglas:

- Si dos tipos parecen útiles, elige el eje dominante; si sobra información, **vista general +
  detalle**, nunca un diagrama que lo intente todo.
- Mermaid sigue siendo el formato embebido y versionable por defecto en Markdown. `.drawio` es
  obligatorio para despliegue con iconos. **Excalidraw** se usa para diagramas explicativos y
  conceptuales que necesitan libertad espacial y evidencia. **HTML interactivo** se usa cuando
  el valor es recorrer un flujo paso a paso o comparar modos (AS-IS/TO-BE, dev/prod).
- Un diagrama Excalidraw o interactivo **complementa** al Mermaid dueño; nunca lo reemplaza ni
  introduce elementos que el artefacto dueño no tenga.

## 4. Multi-zoom: resumen, límites, detalle

Un diagrama completo funciona como un mapa con fronteras y nombres de calles:

1. **Nivel 1 — Resumen.** Una línea de flujo (`Canal → Borde → Aplicación → Datos`) visible de
   un vistazo, arriba o abajo.
2. **Nivel 2 — Límites.** Regiones rotuladas (sistema, bounded context, zona de confianza,
   VPC/VNet, ambiente) que dicen qué va junto.
3. **Nivel 3 — Detalle.** Dentro de cada región, la evidencia que enseña (§5).

En Mermaid el nivel 3 suele ir en el texto o en el diagrama de detalle; en Excalidraw y en el
interactivo puede vivir dentro del mismo lienzo (panel de paso, bloque de evidencia).

## 5. Evidencia concreta

Los diagramas técnicos muestran **lo que las cosas realmente son**, tomado de los artefactos
dueños, no inventado:

| Evidencia | De dónde sale | Cómo se muestra |
|---|---|---|
| Nombres reales de operaciones y eventos | `14.00`, contratos `14.xx.y` | `POST /v1/pagos`, `PagoAprobado` en etiquetas o pasos |
| Payload de ejemplo | Contrato OpenAPI/AsyncAPI | Bloque de código en Excalidraw o panel del interactivo |
| Protocolo, puerto, autenticación | `14.xx`, `17` | `HTTPS · mTLS · :443`, chips del paso |
| Requisito de seguridad que aplica | `19.1` | Chip `SEC-004` en el paso o nodo |
| Latencia/volumen esperado | `05`, `QA-xx` | Chip `p95 < 300 ms` |
| Decisión que lo justifica | `20` | Nota `DA-012` |

Nunca inventes evidencia para llenar el lienzo: si no está en un artefacto dueño, va como
supuesto en `04` o no va.

## 6. Audiencia y diales de salida

| Dial | Opciones | Efecto |
|---|---|---|
| Audiencia | `ingenieria` · `mixta` · `ejecutiva` | Cambia **vocabulario y detalle**, no la verdad: ejecutiva = capacidades y riesgos sin tecnología; ingeniería = protocolos, puertos, IDs |
| Detalle | `fiel` (≤24 nodos, zonificado) · `balanceado` (≤12) · `simplificado` (≤7) | `fiel` solo para importaciones o despliegue; respeta el presupuesto de la guía de calidad |
| Tamaño | `documento` · `documento-ancho` · `diapositiva-16x9` · `impresion-a3` | Lienzo y tamaño de letra para `25.1` o PDF |
| Formato | Mermaid · `.drawio` · `.excalidraw` · HTML interactivo · PNG/SVG exportado | Ver §3 y §11 |

Un diagrama que intenta servir a negocio y a ingeniería a la vez no sirve a ninguno: genera
dos vistas del mismo modelo.

## 7. Diagramas de cambio (AS-IS → TO-BE)

Para Caso C (`23`, `24`) y para cambios de alternativa:

- Dos vistas **sincronizadas** (misma posición para lo que no cambia) o un interactivo con
  modos `AS-IS`/`TO-BE`.
- Clases `nuevo`, `retirado` y `modificado` (borde verde, rojo punteado, ámbar) explicadas en
  leyenda; lo que no cambia en neutro.
- **Bitácora de cambios** debajo: tabla `Elemento · Cambio · Motivo (DA/BR) · Fase de 24`.
- Si solo cambian atributos (versión, tamaño), usa una tabla, no un delta visual.

## 8. Accesibilidad

- El color nunca es el único diferenciador: combínalo con forma, borde (continuo/discontinuo)
  o etiqueta; el diagrama debe leerse en escala de grises.
- Contraste mínimo de texto 4.5:1 sobre su fondo; texto ≥ 12 px en el tamaño de exportación.
- Leyenda como franja inferior, nunca flotando entre nodos.
- SVG/HTML: `role="img"`, `<title>` y `<desc>` con IDs únicos; en el interactivo, anuncios
  `aria-live` por paso y navegación por teclado.
- Sin texto vertical ni rotado.

## 9. Bucle renderizar → mirar → corregir

Ningún diagrama se juzga solo por su fuente. Antes de cerrar:

1. **Valida la estructura** con el script del formato (`validate_mermaid.py`,
   `validate_drawio_catalog.py` + `validate_drawio_layout.py`, `validate_excalidraw.py`,
   `build_interactive_diagram.py --check`).
2. **Renderiza y mira.** `python scripts/render_preview.py <archivo> -o <png>` genera una vista
   previa aproximada de `.drawio` y `.excalidraw` sin dependencias externas; ábrela con la
   herramienta de visualización de imágenes. Si hay draw.io CLI/Docker o el MCP permite
   exportar, prefiere el render real (§11).
3. **Audita contra el plan** (§2): ¿la estructura visual coincide con la conceptual? ¿el ojo
   recorre el orden previsto? ¿el foco es el foco?
4. **Busca defectos**: texto cortado o desbordado, solapamientos, flechas que cruzan nodos o
   terminan en el vacío, etiquetas ambiguas, espaciado desigual, zonas vacías junto a zonas
   saturadas, texto ilegible al tamaño final.
5. **Corrige y repite** (2–4 vueltas es normal). Termina cuando lo mostrarías al comité sin
   advertencias.

Registra en el criterio de cierre del artefacto qué se validó y qué se miró (o que no se pudo
renderizar y por qué).

## 10. Importar diagramas existentes

Cuando el insumo es un `.drawio`, `.excalidraw`, Mermaid o una imagen del cliente:

1. **Extrae, no copies.** Obtén componentes, relaciones, agrupaciones y dirección
   (`extract_drawio_inventory.py`, `validate_excalidraw.py --inventory`, lectura del Mermaid).
2. **Redibuja con la notación de archi.** Coordenadas, colores y estilos de origen se descartan.
3. **Bitácora de fidelidad**: qué se fusionó, colapsó, renombró o dejó fuera y por qué. Nunca
   inventes un componente para completar el layout ni elimines uno en silencio.
4. En Caso B, lo importado es evidencia AS-IS: cita la fuente y su fecha.

## 11. Exportar y publicar

- **draw.io → PNG/SVG** para `25.1`, PDF o wikis:
  `drawio --export --format png --scale 2 --border 20 --embed-diagram -o <archivo>.drawio.png <archivo>.drawio`
  o, sin escritorio, `docker run --rm -w /data -v "$PWD":/data rlespinasse/drawio-desktop-headless --export --format svg --embed-diagram -o <archivo>.drawio.svg <archivo>.drawio`.
  `--embed-diagram` mantiene el PNG/SVG editable en draw.io. Versiona `.drawio` y su export.
- **Excalidraw → PNG/SVG**: exporta desde el MCP o la app con "embed scene" para conservar la
  edición; versiona el `.excalidraw`.
- **Mermaid en Azure DevOps**: los wikis de Azure DevOps usan `:::mermaid` … `:::`; GitHub y
  Markdown estándar usan el bloque ` ```mermaid `. Detecta la plataforma por el remoto
  (`dev.azure.com`/`visualstudio.com`) cuando el documento se publique en un wiki, sin cambiar
  la fuente canónica de `resources/architecture/`.
- **HTML interactivo**: un solo archivo autocontenido, abrible sin conexión; enlázalo desde
  `15` y desde `25.1`.

## 12. Checklist de explicación

- [ ] Pregunta, audiencia, patrón, tipo/herramienta y recortes declarados.
- [ ] Pasa la prueba de isomorfismo y la de aprendizaje.
- [ ] Multi-zoom presente en diagramas técnicos completos.
- [ ] Evidencia concreta tomada de artefactos dueños, sin inventar.
- [ ] Color acompañado de forma/borde/etiqueta; leyenda en franja inferior.
- [ ] Validado estructuralmente **y** renderizado y mirado (o motivo registrado).
- [ ] Diagramas complementarios coherentes con su Mermaid/`.drawio` dueño (mismos IDs y nombres).
