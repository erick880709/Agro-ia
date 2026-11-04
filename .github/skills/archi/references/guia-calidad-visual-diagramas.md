# Guía: Calidad visual de diagramas

Esta guía es la **dueña de las reglas de diagramación** de `archi`. Aplica a todo diagrama: alternativas (`09`), C4 (`14`, `14.xx`), secuencias (`15`), datos (`16.xx`), tácticas (`18`), amenazas (`19.1`) y despliegue (`17`, `17.1`-`17.3`). `drawio-iconos-nube.md` define qué icono usar; esta guía define cómo se dibuja. Léela antes del primer diagrama de la sesión.

Un diagrama correcto en contenido pero desordenado transmite descuido y resta credibilidad ante un Comité de Arquitectura. Trátalo con el mismo rigor que el texto.


Antes de aplicar estas reglas, decide qué dibujar con `references/guia-diseno-diagramas.md`
(pregunta, audiencia, patrón semántico, tipo y herramienta, multi-zoom, evidencia y bucle
renderizar → mirar → corregir). Para Excalidraw sigue además `references/guia-excalidraw.md`
y para recorridos paso a paso `references/guia-diagramas-interactivos.md`; las reglas de esta
guía aplican a los tres formatos.

## 1. Principios

1. **Un diagrama responde una pregunta.** Escríbela antes de dibujar ("¿qué unidades se despliegan por separado en la alternativa B?"). Si no puedes formularla, el diagrama sobra o mezcla dos vistas.
2. **Nada real se omite; lo redundante sí.** Un componente que existe en el texto existe en el diagrama. Si el diagrama excede el presupuesto (§5), se divide en vista general + detalle; nunca se borra información para que "se vea ordenado".
3. **Prueba de eliminación** antes de cerrar:
   - ¿Dos nodos siempre aparecen juntos y nunca se hablan por separado? Fusiónalos.
   - ¿Una conexión ya es evidente por contención (componente dentro de su contenedor)? Quítala.
   - ¿Una etiqueta repite el nombre del nodo? Redúcela a verbo + protocolo.
   - ¿Más de dos elementos destacados? Decide cuál es el foco; el resto va neutro.
4. **Coherencia entre diagramas hermanos.** Las alternativas de `09`, los niveles C4 y los tres `.drawio` usan la misma orientación, notación y vocabulario; si una diferencia visual no representa una diferencia arquitectónica, es ruido.
5. **Declara el plan antes de dibujar**: qué diagramas, formato, pregunta de cada uno y qué se divide por presupuesto. Si el usuario está disponible, deja que lo redirija.

## 2. Notación estándar para Mermaid `flowchart`

Usa siempre esta notación en diagramas lógicos (`09`, fallback de despliegue, dependencias, decisiones de `18`). El lector aprende la notación una vez y la reconoce en todo el paquete.

| Elemento | Forma Mermaid | Ejemplo |
|---|---|---|
| Persona o canal | estadio `([ ])` | `U([Cliente web])` |
| Unidad desplegable (servicio, worker, función, frontend) | rectángulo `[ ]` | `API[CT-01 API de Pedidos]` |
| Almacenamiento (BD, caché, blob) | cilindro `[( )]` | `DB[(DATA-001 Pedidos)]` |
| Broker, cola o topic | subrutina `[[ ]]` | `Q[[Eventos de pedido]]` |
| Decisión o regla | rombo `{ }` | `D{¿Pago aprobado?}` |
| Sistema externo | rectángulo con `:::ext` | `PSP[EXT-01 Pasarela]:::ext` |
| Límite (sistema, dominio, red, zona de confianza) | `subgraph` con título | `subgraph SOL["Solución"]` |

Conectores:

| Significado | Sintaxis |
|---|---|
| Llamada síncrona | `A -->|"REST/JSON · crea pedido"| B` |
| Mensaje asíncrono o evento | `A -.->|"AMQP · PedidoCreado"| B` |
| Dependencia prohibida o eliminada (AS-IS/TO-BE, capas) | `A -.-x|"no debe depender"| B` |

Clases de estilo (declara solo las que uses y explícalas en la leyenda):

```text
classDef ext stroke-dasharray:5 5,fill:#ffffff,stroke:#6B778C,color:#42526E
classDef foco fill:#FFF4E5,stroke:#C25100,stroke-width:2px
classDef nuevo stroke:#1F845A,stroke-width:2px
classDef retirado stroke:#AE2E24,stroke-dasharray:3 3,color:#AE2E24
```

`foco` se aplica a dos elementos como máximo. `nuevo` y `retirado` solo en Caso C o en `09` cuando la alternativa conserve parte del AS-IS.

**Leyenda.** Todo diagrama que use `ext`, `foco`, `nuevo`, `retirado` o conectores punteados lleva debajo una línea de leyenda en Markdown (`**Leyenda:** línea punteada = asíncrono; borde discontinuo = sistema externo; …`). No metas la leyenda como nodo dentro del grafo: compite con los nodos reales por espacio de layout.

## 3. Reglas de conectores

1. **Ortogonales, nunca curvos.** En Mermaid `flowchart`/`graph`, declara la curva en el frontmatter del bloque:

   ````text
   ```mermaid
   ---
   config:
     flowchart:
       curve: step
   ---
   flowchart LR
       ...
   ```
   ````

   `step` produce ángulos rectos. El valor por defecto (`basis`) dibuja curvas y `linear` dibuja diagonales; ninguno de los dos es aceptable. `C4*`, `sequenceDiagram`, `erDiagram`, `classDiagram` y `stateDiagram` tienen su propio trazado y no usan esta directiva. En `.drawio`: `edgeStyle=orthogonalEdgeStyle;rounded=0;curved=0;` en cada conector.
2. **Dirección única y explícita.** `LR` para flujos de petición (canal → borde → aplicación → datos) y despliegue; `TB` para jerarquías y dependencias de capas. Nunca dejes que Mermaid decida.
3. **Toda conexión lleva etiqueta** con verbo y protocolo, máximo ~40 caracteres: `"SQL/TLS · lee y escribe"`, `"AMQP · PedidoCreado"`. La única excepción es la contención obvia.
4. **Sin solapamientos ni tránsito por nodos ajenos.** Un conector no pasa por detrás de un nodo que no es su origen ni su destino, y dos conectores no comparten el mismo tramo. En Mermaid se resuelve con el orden de declaración y agrupando en `subgraph`; en `.drawio`, con anclajes y waypoints (§7).
5. **Anclajes repartidos.** Si tres o más conectores salen del mismo lado de un nodo, asígnales puntos distintos (`exitX`/`exitY` en `.drawio`) en vez de dejarlos converger en el centro.

## 4. Orden y agrupación

- Declara los nodos en el orden de lectura. Mermaid respeta bastante el orden de declaración: actores primero, luego borde, aplicación, datos y externos.
- Dibuja los límites reales (sistema, bounded context, zona de confianza, VPC/VNet, subred, región) como `subgraph`/contenedor. No dibujes límites sin soporte documental y no dejes nodos sueltos si existe un límite que los agrupa.
- En `19.1`, los trust boundaries del modelo de amenazas son `subgraph` con el prefijo `TB-` para que la tabla de amenazas y el diagrama se lean juntos.

## 5. Presupuesto de complejidad

Por encima de estos límites, divide en vista general + detalle (por bounded context, por zona de red o por flujo).

| Diagrama | Máximo |
|---|---|
| Alternativa lógica (`09`) | 12 nodos, 18 conectores |
| C4 Nivel 1 | 1 sistema + 8 elementos externos |
| C4 Nivel 2 | 12 elementos |
| C4 Nivel 3 (por `14.xx`) | 10 componentes |
| Secuencia | 7 participantes, 25 mensajes, 1 nivel de anidación `alt`/`opt` |
| Entidad-relación (por `16.xx`) | 10 entidades |
| Despliegue `.drawio` (por página) | 15 recursos, 18 conectores, 3 niveles de contenedores |
| Cualquiera | 2 elementos destacados |

## 6. Reglas por tipo de diagrama

**Alternativas (`09`).** Mismo `flowchart LR`, misma notación y misma granularidad en todas las alternativas, de modo que la única diferencia visible sea la estructural (qué se separa, qué se comparte, qué se comunica de forma asíncrona). Cloud-agnóstico: nombres lógicos ("Broker de eventos"), nunca productos ("Azure Service Bus").

**C4 en Mermaid.** El renderizador C4 de Mermaid es experimental y tiende a apilar etiquetas. Para que se lea:

- Declara `UpdateLayoutConfig($c4ShapeInRow="3", $c4BoundaryInRow="1")` y ajusta el número por fila según el ancho.
- Declara los elementos en el orden de lectura y agrupa con `System_Boundary`/`Container_Boundary`.
- Toda `Rel` lleva descripción **y** tecnología: `Rel(api, db, "Lee y escribe pedidos", "SQL/TLS")`.
- Si dos etiquetas se pisan, separa con `UpdateRelStyle(origen, destino, $offsetY="-20")`.
- Los contenedores muestran su ID: `Container(api, "CT-01 API de Pedidos", "Java 21 / Spring Boot", "…")`.
- Si un Nivel 2 supera 12 elementos aún agrupado, divide por dominio; no fuerces el renderizador.

**Secuencias (`15`, `18`).**

- `autonumber` siempre, para poder citar pasos desde el texto ("en el paso 6…").
- Participantes en el orden real del flujo, de izquierda a derecha, con el ID: `participant API as CT-01 API de Pedidos`.
- Los flujos críticos muestran al menos una ruta de error con `alt`/`else` u `opt`/`break`; un camino feliz solo no es un flujo crítico documentado.
- Usa `activate`/`deactivate` o `+`/`-` cuando el tiempo de procesamiento o la concurrencia importen.
- Escritura y publicación de eventos en el mismo flujo: muestra el mecanismo de consistencia (outbox, transacción, idempotencia); no dibujes un *dual write* sin señalarlo como riesgo.

**Entidad-relación (`16.xx`).** Entidades del mismo agregado declaradas juntas; cardinalidades explícitas; PK/FK marcadas; nombres de relación como verbos.

**Despliegue `.drawio` (`17.1`-`17.3`).** Ver §7 y `drawio-iconos-nube.md`.

## 7. Composición de `.drawio`

1. **Columnas por capa**, izquierda a derecha: canales y externos → borde (DNS, CDN, WAF, gateway) → aplicación → integración → datos → operación (observabilidad, secretos, identidad). Todos los nodos de una columna comparten `x`; los de una fila, `y`.
2. **Grilla de 10 px** para posiciones (`gridSize="10"`; `x` e `y` múltiplos de 10). Íconos de 64-78 px (72 px por defecto), del **mismo tamaño** en toda la página.
3. **Contenedores anidados** cuenta › región › red › subred, con los estilos de límite del catálogo (AWS) o cajas neutras rotuladas (Azure/GCP). Ningún nodo se sale de su contenedor.
4. **Conectores** con `edgeStyle=orthogonalEdgeStyle;rounded=0;curved=0;`, etiqueta en cada uno, anclajes `exitX/exitY/entryX/entryY` cuando haya tres o más conectores en un lado, y waypoints (`<Array as="points">`) para rodear nodos en vez de atravesarlos.
5. **Síncrono continuo, asíncrono/control/telemetría discontinuo**, explicado en una leyenda dentro de la página.
6. **Etiqueta de nodo** = componente real · servicio (`CT-01 API de Pedidos · App Service`). Nunca solo el nombre del producto.

## 8. Validación automática

Una regla que solo vive en prosa termina entregándose rota. Ejecuta antes de cerrar cada artefacto con diagramas:

```bash
# Mermaid: reglas de esta guía + compilación real con el parser oficial
python scripts/validate_mermaid.py resources/architecture/*.md --node-modules <dir>/node_modules --strict

# draw.io: catálogo de iconos y luego composición
python scripts/validate_drawio_catalog.py --drawio <archivo> --provider <azure|aws|gcp> --strict
python scripts/validate_drawio_layout.py --drawio <archivo> --strict
# Excalidraw: estructura, vinculaciones, ortogonalidad, paleta, solapamientos y IDs del dueño
python scripts/validate_excalidraw.py <archivo>.excalidraw --strict --owner <dueño>.md
# Diagrama interactivo: especificación + HTML autocontenido
python scripts/build_interactive_diagram.py <spec>.json -o <salida>.html --strict --owner <dueños>.md
# Vista previa para MIRAR el resultado (.drawio y .excalidraw)
python scripts/render_preview.py <archivo> -o /tmp/<archivo>.png
```

Instalación única del parser Mermaid (Node 18+): `npm install --prefix <dir> mermaid@11.4.1 jsdom@25.0.1`. Si no está disponible, `validate_mermaid.py` lo informa como advertencia: en ese caso registra en el criterio de cierre que la compilación no se verificó; nunca la declares verificada.

| Script | Verifica | No puede verificar |
|---|---|---|
| `validate_mermaid.py` | Compilación, dirección, curva, etiquetas, presupuesto, `autonumber`, ruta de error, tecnología en `Rel`, layout C4 | Si el layout final se lee bien; cruces en el render |
| `validate_drawio_catalog.py` | Biblioteca, proveedor, `archiIconId`, estilo canónico | Composición |
| `validate_excalidraw.py` | JSON, IDs, vinculaciones bidireccionales, ortogonalidad, paleta, solapamientos, desbordes, etiquetas que no caben, leyenda, presupuesto, IDs del dueño | Composición fina; render real de Excalidraw |
| `build_interactive_diagram.py` | Especificación (IDs, roles, modos, pasos, rutas de error, IDs del dueño) y generación segura del HTML; en la página, `archValidate()` | Calidad narrativa de cada paso |
| `render_preview.py` | Genera PNG aproximado para revisión visual y reporta etiquetas superpuestas o sobre nodos | Fidelidad exacta al render de la herramienta |
| `validate_drawio_layout.py` | Conectores ortogonales y etiquetados, extremos válidos, tránsito por nodos ajenos, solapamientos, desbordes, tamaños, grilla, anclajes, leyenda, presupuesto | Estética fina y legibilidad de etiquetas largas |

Lo que los scripts no ven se revisa con la checklist.

## 9. Checklist antes de cerrar un diagrama

- [ ] Responde una pregunta explícita y coincide con el texto en ambos sentidos.
- [ ] Notación estándar (§2) y leyenda si usa estilos o líneas punteadas.
- [ ] Conectores ortogonales, etiquetados con verbo + protocolo, sin tránsito por nodos ajenos.
- [ ] Una sola dirección de lectura, declarada.
- [ ] Límites reales dibujados como contenedor.
- [ ] Dentro del presupuesto, o dividido en vista general + detalle.
- [ ] Máximo dos elementos destacados.
- [ ] IDs estables visibles (`CT-xx`, `EXT-xx`, `DATA-xxx`, `TB-xx`).
- [ ] Validadores ejecutados sin errores y resultado registrado en el criterio de cierre.
- [ ] Renderizado y **mirado** (`render_preview.py`, export real o navegador) con el bucle de `guia-diseno-diagramas.md` §9; defectos corregidos.
- [ ] Pasa las pruebas de isomorfismo y de aprendizaje; evidencia concreta tomada de artefactos dueños.
