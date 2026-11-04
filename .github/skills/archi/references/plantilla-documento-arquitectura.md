# Plantilla: Documento de Arquitectura de Software

Estructura dividida y numerada según el orden de generación. Está inspirada en arc42, C4, ATAM/QAW y Well-Architected, e incorpora gates de selección, experimentación y aprobación. Omite archivos condicionales sin renumerar los restantes. `00` se genera al final, aunque ordena primero.

## Por qué este orden

1. La línea base, el contexto, las restricciones, los supuestos, los atributos de calidad y las funcionalidades significativas (`01`-`06`) constituyen los drivers.
2. El QAW (`07`) valida y prioriza los drivers antes de aplicar Well-Architected (`08`) y comparar alternativas (`09`).
3. La selección (`10`), el arquetipo/baseline tecnológico (`10.1`), la evaluación de tecnologías (`11`), las incertidumbres (`12`) y las PoC (`13`) evitan detallar una solución no aceptada o técnicamente inviable.
4. Las vistas de diseño (`14`-`19`) describen la alternativa ya seleccionada y validada. `14` y `16` funcionan como índices maestros; `14.00` gobierna transversalmente las APIs y el detalle vive por contenedor significativo en `14.xx` y `16.xx`.
5. Decisiones, riesgos y glosario (`20`-`22`) consolidan el diseño; brechas y roadmap (`23`-`24`) solo aplican al TO-BE.
6. La revisión (`25`), la presentación trazable (`25.1`) y la aprobación humana (`26`) cierran el proceso. El orquestador `00` resume únicamente la versión aprobada.

## Estructura de archivos

| # | Archivo | Contenido | Aplicación |
|---|---|---|---|
| 00 | `00-Documento_Arquitectura_<Proyecto>.md` | Orquestador de 100-150 líneas: propósito, resumen ejecutivo, stakeholders, estado de aprobación e índice. Para B/C usa `00-Arquitectura_AS-IS_<Proyecto>.md` o `00-Arquitectura_TO-BE_<Proyecto>.md` | Todos; se genera al final |
| 01 | `01-Linea-Base_<Proyecto>.md` | Gate DR-01 de preparación del dominio, fuentes revisadas, contexto confirmado, stack, nube, gobierno, responsable de selección y autoridad de aprobación | A y C |
| 02 | `02-Contexto-y-Alcance.md` | Objetivos de negocio `OBJ-xx`, RF clave, tabla de interesados, 3-5 objetivos de calidad top, C4 Contexto y tabla de contexto técnico | Todos |
| 03 | `03-Restricciones.md` | Restricciones técnicas (`RT-Dxx`), de negocio/normativas (`RN-Dxx`) y de recursos (`RR-Dxx`), fuente y negociabilidad | Todos |
| 04 | `04-Supuestos.md` | Supuestos `SUP-Dxx`, confianza y plan de validación; documento vivo | Todos |
| 05 | `05-Atributos-de-Calidad.md` | Tabla resumen de priorización y escenarios `QA-xx`: descripción, `OBJ-xx`, atributos relevantes, componentes SEI, preguntas, problemas, prioridad y validación | A/C; evidencia real en B |
| 06 | `06-Funcionalidades-Significativas.md` | Funcionalidades `FAS-xxx` y drivers que afectan la arquitectura | A/C; evidencia real en B |
| 07 | `07-Resultado-QAW.md` | Participantes, escenarios priorizados, votos, trade-offs, decisiones, compromisos, lecciones aprendidas, pendientes y matriz de cobertura de los 13 atributos | A y C |
| 08 | `08-Well-Architected.md` | Matriz de cobertura de los 6 pilares y principios/prácticas (`PD-xx`/`BP-xxx`) por pilar, enriquecidos por los `QA-xx` priorizados; cuando aplique, revisión por pregunta con estado, evidencia y riesgo HRI/MRI y lentes de dominio | A y C |
| 08.1 | `08.1-WA-Tool_<Proyecto>.json` | Exportación a AWS Well-Architected Tool con identificadores obtenidos de la herramienta | Si el cliente usa la herramienta |
| 09 | `09-Alternativas-de-Solucion.md` | Mapa común de alcance y configuraciones consolidada/híbrida/distribuida: cada opción bajo `### Alternativa <ID> — <Nombre>` con su propio diagrama lógico Mermaid; asignación de cada capacidad a módulos, servicios, workers, funciones o administrados; composición frontend SPA modular/Microfrontends cuando cambie la topología; nube, trade-offs y recomendación | A y C |
| 10 | `10-Seleccion-de-Arquitectura.md` | Configuración seleccionada, matriz aprobada de asignación por alcance, autoridad, fecha, condiciones, riesgos aceptados, estado y síntesis de estrategia | A y C |
| 10.1 | `10.1-Arquetipo-de-Solucion_<Proyecto>.md` | Análisis de arquetipos con la profundidad estructural de `05.04.06-Analysis-Archetypes.md`: `ARQ-xxx`, inventario y ficha por scaffold con árbol de carpetas, patrones, contrato de desarrollo, configuración y aceptación; componentes compartidos, convenciones, prioridad, relación con legado, decisiones de framework y baseline tecnológico; sigue `references/guia-arquetipo-solucion.md` sin copiar las tecnologías del ejemplo | Todos; seleccionado en A/C, observado en B |
| 11 | `11-Evaluacion-Tecnologias-Emergentes.md` | Madurez, soporte, seguridad, operación, lock-in, contingencia y decisión | Condicional |
| 12 | `12-Registro-de-Incertidumbres.md` | Hipótesis, impacto, confianza, validación, umbral, responsable y estado | A y C |
| 13 | `13-Plan-y-Resultados-PoC.md` | Hipótesis, timebox, métricas, umbrales, evidencia, resultados y decisión | Si hay incertidumbre crítica |
| 14 | `14-Vistas-C4.md` | C4 Nivel 2, inventario `CT-xx`, clasificación de significancia y matriz de cobertura; enlaza un `14.xx` con C4 Nivel 3 por contenedor significativo | Todos |
| 14.00 | `14.00-Gobierno-y-Catalogo-Inicial-de-APIs_<Proyecto>.md` | Estándar de nomenclatura, buenas prácticas adoptadas, seguridad, compatibilidad, ciclo de vida y catálogo canónico `API-xxx`/`API-xxx-OP-xxx`; sigue `references/guia-gobierno-y-diseno-apis.md` | Cuando existan APIs, eventos, RPC, webhooks u otras interfaces programáticas |
| 14.xx | `14.xx-Diseno-Detallado_CT-xx_<Contenedor>.md` | Diseño detallado del contenedor: C4 Nivel 3, organización interna (Hexagonal/Capas cuando aplique), componentes, contratos, CQRS localizado, tácticas/patrones, reglas `CC-xxx`, seguridad, resiliencia, observabilidad y riesgos | Cada contenedor significativo |
| 15 | `15-Secuencias.md` | Secuencias de flujos críticos y rutas de error relevantes | Todos |
| 16 | `16-Modelo-de-Datos.md` | Catálogo canónico `DATA-xxx`, mapa global de ownership y flujos de datos; índice de modelos por contenedor | Cuando exista información/estado relevante |
| 16.xx | `16.xx-Modelo-de-Datos_CT-xx_<Contenedor>.md` | Tipo de motor elegido y justificación; objetivo y madurez conceptual/lógica/física; matriz `driver → API/schema → DATA → entidad → estructura/store`; ER, agregados, consistencia, transacciones y, si aplica, comandos/proyecciones CQRS; cuando exista nivel físico, diccionario exhaustivo por objeto/campo según `references/guia-diccionario-fisico-datos.md`; seguridad, retención y recuperación | Cada contenedor significativo con estado relevante |
| 16.xx.y | `16.xx.y-Schema_<DATA-xxx>.<sql|dbml|prisma|otro>` | Esquema físico procesable, migración/versionado y evidencia de validación | Cuando el objetivo sea listo para implementación, el usuario pida modelo físico o el esquema sea condición de migración/estimación |
| 17 | `17-Vista-de-Despliegue.md` | Topología, ambientes, patrones cloud aplicados y enlaces a `17.1`-`17.5` | Condicional |
| 17.6 | `17.6-Infraestructura-Base_<Proyecto>.md` | Organización/cuentas, identidad de máquinas y accesos entre cuentas, red y segmentación, inspección/egress/híbrido/DNS, registro central, runners de CI/CD, reporte de banderas y diagramas `17.6.N`; sigue `references/guia-infraestructura-cloud.md` | Multi-cuenta, red compartida, híbrido, inspección, sector regulado o runners con acceso privado |
| 17.7 | `17.7-Blueprint-IaC_<Proyecto>.md` | Inventario `17.7.1` extraído de los `.drawio`, módulos exclusivos, secuencia, contratos, permisos derivados de conectores, guardrails, especificación de código y handoff; sigue `references/guia-diagrama-a-iac.md` | A/C cuando se pida pasar a implementación o el entregable deba quedar listo para construir |
| 17.4.1 | `17.4.1-Costos_<Proyecto>.json` | Partidas, unidades, evidencia de tarifas, escenarios y asignaciones por ambiente; fuente de totales `17.4`/`17.5` según `references/contrato-costos.md` | Cuando se genere o revise pricing |
| 18 | `18-Tacticas-y-Patrones.md` | Catálogo maestro `TP-xxx` de tácticas arquitectónicas y patrones arquitectónicos, de diseño, cloud e IA: cobertura `QA → TP → CT → DA → prueba`, fichas con mecanismo/configuración/fallos/trade-offs/operación/validación y Mermaid cuando aporte explicación; sigue `references/guia-tacticas-patrones.md` y `references/guia-catalogo-patrones.md` | Todos |
| 19 | `19-Dimensiones-Arquitectonicas.md` | Integraciones, datos/analítica, IA y patrones IA, seguridad, calidad/pruebas, catálogo `CC-xxx` de Clean Code, observabilidad, UX/i18n y low-code | Todos |
| 19.1 | `19.1-Modelo-de-Amenazas-y-Requisitos-de-Seguridad_<Proyecto>.md` | Activos, datos, superficies, fronteras de confianza, amenazas `THR-xxx`, escenarios de abuso, requisitos verificables `SEC-xxx`, riesgo residual y contrato de entrega a Vulcano; sigue `references/guia-modelo-amenazas-y-requisitos-seguridad.md` | Condicional según exposición, sensibilidad, regulación o riesgo |
| 20 | `20-Decisiones-Arquitectonicas.md` | Consolida decisiones `DA-xxx` registradas en artefactos previos, con estado, consecuencias y validación. Después queda vivo durante revisión/aprobación; enlaza `09`-`10` para configuración/nube | Todos |
| 21 | `21-Riesgos-y-Deuda-Tecnica.md` | Riesgos, mitigación y deuda/hallazgos AS-IS | Todos |
| 22 | `22-Glosario.md` | Términos de dominio y siglas no evidentes | Todos |
| 23 | `23-Analisis-de-Brechas.md` | Diferencias AS-IS/TO-BE, esfuerzo y riesgo | Solo C |
| 24 | `24-Roadmap-de-Migracion.md` | Fases incrementales, validación y rollback | Solo C |
| 25 | `25-Revision-Tecnica-Arquitectura.md` | Auditoría formal: snapshot/hash, criterios, prometido versus diseñado, trazabilidad bidireccional, contradicciones/huérfanos, coherencia por dimensión, ATAM, indicadores, dictamen y validación automática; sigue `references/guia-auditoria-coherencia-arquitectura.md` | Todos |
| 25.1 | `25.1-Presentacion-Comite-Arquitectura_<Proyecto>.html` + `25.1.1-Manifiesto-Presentacion_<Proyecto>.json` | Presentación ejecutiva/técnica con decisión solicitada, evidencia del trabajo, alternativas, diseño, validación, riesgos y trazabilidad a fuentes; sigue `references/guia-presentacion-comite-arquitectura.md` | Todos; después de `25` y antes de `26` |
| 26 | `26-Validacion-y-Aprobacion.md` | Participantes, versiones revisadas, observaciones, condiciones, compromisos, lecciones aprendidas y decisión humana | Todos |

## Tabla de contenido por artefacto

Cada Markdown generado, salvo `00`, empieza con esta sección justo después del título (y el
comentario `<!-- Document ID -->` y la línea de contexto inicial, si existen) y antes del primer
encabezado de contenido:

```markdown
## Tabla de Contenido
- [Nombre del encabezado ##](#anchor-generado)
- [Nombre del encabezado ##](#anchor-generado)
  - [TP-001 — Nombre de la ficha](#tp-001-nombre-de-la-ficha)
  - [TP-002 — Nombre de la ficha](#tp-002-nombre-de-la-ficha)
- [Criterios de cierre](#criterios-de-cierre)
```

Reglas:

- Enlaza todos los encabezados `##` del documento, incluida la propia `## Criterios de cierre` final.
- Cuando un `##` organiza entradas catalogadas con ID estable en `###`/`####` (`TP-xxx`, `DA-xxx`, `QA-xx`, `ARQ-xxx`, `Alternativa <ID>`, Análisis ATAM por `QA-xx`, `SEC-xxx`, `THR-xxx`, `CC-xxx`), anida un enlace por entrada bajo el `##` que las contiene.
- No enlaces subsecciones de ficha que se repiten idénticas dentro de cada entrada (p. ej. "Problema y contexto", "Mecanismo", "Trade-offs" de cada `TP-xxx`, o los campos fijos de cada `DA-xxx`): agregan ruido sin valor de navegación adicional.
- Usa el texto real del encabezado como texto del enlace y el anchor que genera Markdown a partir de él (minúsculas, espacios por guiones, sin puntuación); no inventes anchors distintos al encabezado real.
- Actualízala junto con el resto del documento: un encabezado agregado, renombrado o quitado sin reflejarse aquí deja el artefacto en `No cumple`.
- `00-Documento_Arquitectura_<Proyecto>.md` (y sus variantes AS-IS/TO-BE) no repite esta sección: su `## Índice`, que enlaza a los demás documentos, cumple la misma función de navegación para un orquestador de 100-150 líneas.

## Criterios de cierre por artefacto

Además de los criterios propios de cada artefacto, todo Markdown generado (salvo `00`) debe
conservar una `## Tabla de Contenido` sincronizada con sus encabezados como precondición para
cerrar en **Cumple** o **Cumple con observaciones**.

Cada Markdown generado termina con una sección `## Criterios de cierre` que copia los criterios aplicables de esta tabla como checklist; convierte cada condición separada por punto y coma en un ítem independiente. Un criterio se marca `[x]` solo cuando el documento contiene o enlaza evidencia verificable; no se acepta marcarlo por intención. Usa uno de estos estados para el artefacto: **Cumple**, **Cumple con observaciones**, **No cumple** o **No aplica**.

- Todos los criterios aplicables de la tabla son obligatorios: uno sin cumplir deja el artefacto en **No cumple**. **Cumple con observaciones** exige todos los criterios cumplidos y solo admite mejoras adicionales no bloqueantes con responsable y fecha.
- **No cumple** impide cerrar el artefacto o sus dependientes y superar el siguiente gate. Se permite elaborar documentos relacionados en paralelo, pero permanecen en borrador y deben revalidarse al cerrar la dependencia.
- **No aplica** requiere motivo escrito en el documento dueño o índice; no se crea un archivo condicional vacío para registrar este estado.
- Si solo una condición interna no aplica, regístrala como `- [x] N/A — [motivo]`; el artefacto conserva su estado global. No uses `N/A` para evitar evidencia disponible o una obligación del escenario.
- En `04`, `10.1`, `14.00` y `20`, que son documentos vivos, los criterios se evalúan al generarlos y nuevamente en `25`.
- `05` es una excepción temporal: en A/C nace como borrador y puede avanzar únicamente a `07`, que permite completar su prioridad; debe quedar actualizado y en `Cumple` antes de iniciar `08` o `09`.
- Para `.drawio` y el HTML de costos `17.5`, registra su checklist en `17-Vista-de-Despliegue.md`, bajo una subsección con el nombre, fecha de revisión y SHA-256 del archivo evaluado. Para cada `.drawio` incluye proveedor, `catalogVersion`, commit fuente del catálogo, comando/resultado del validador y excepciones; no uses `--reference` para un entregable. Para el manifiesto/HTML `25.1`, registra el checklist, fecha, hashes y salida del validador en una subsección posterior de `25`.

Formato mínimo:

```markdown
## Criterios de cierre
**Estado:** [Cumple/Cumple con observaciones/No cumple/No aplica]

- [ ] [criterio verificable]
- [ ] [criterio verificable]

**Evidencia u observaciones:** [enlaces, IDs, responsable/fecha o motivo de No aplica]
```

| Artefacto | Criterios de cierre obligatorios |
|---|---|
| `00` | Existe aprobación en `26`; todos los enlaces resuelven; el resumen coincide con selección, arquetipo `10.1`, diseño y `26`; expone condiciones abiertas; conserva 100-150 líneas. |
| `01` | Incluye `## Preparación del dominio` conforme a `references/guia-preparacion-dominio.md`; DR-01 está `Listo` o `Listo con riesgos`, con evidencia verificable, cero hotspots arquitectónicos bloqueantes y ningún handoff pendiente; `Listo con riesgos` identifica riesgos, owner y condición de cierre, y debe actualizarse a `Listo` antes de que `25` sea apto; identifica fuentes revisadas; confirma los bloques críticos de línea base; distingue hechos, inferencias y vacíos; identifica responsable de selección y autoridad de aprobación. |
| `02` | Delimita alcance incluido/excluido; cada objetivo de negocio tiene `OBJ-xx`, medida de éxito y fuente/responsable; identifica interesados; el C4 Contexto coincide con sistemas externos, protocolos y dirección de datos; declara 3-5 objetivos de calidad principales. |
| `03` | Cada restricción tiene ID, tipo, fuente y negociabilidad; no hay contradicciones críticas sin resolver; las restricciones relevantes se trazan a alternativas o decisiones. |
| `04` | Cada supuesto tiene ID, confianza, impacto y plan de validación; todo supuesto crítico tiene responsable; los supuestos invalidados o cerrados conservan estado y evidencia. |
| `05` | Cada `QA-xx` priorizado completa descripción, `OBJ-xx`, atributos relevantes y componentes SEI medibles; preguntas y problemas tienen disposición explícita; la tabla resumen contiene todos los escenarios priorizados; en A/C el orden, prioridad y votos/ranking coinciden con `07`, y en B están sustentados por evidencia AS-IS. |
| `06` | Cada `FAS-xxx` explica por qué es arquitectónicamente significativa y enlaza los `OBJ-xx`, `QA-xx`, restricciones, contenedores o decisiones afectados; no lista funcionalidades triviales. |
| `07` | Registra participantes y mecanismo de priorización; clasifica los 13 atributos, incluida Seguridad; documenta escenarios priorizados, `OBJ-xx`, trade-offs y compromisos; actualiza `05` y `06`. |
| `08` | Clasifica los 6 pilares; cada pilar cubierto enlaza `PD-xx`/`BP-xxx`; todo descarte o `No aplica` tiene motivo; hallazgos alimentan decisiones o riesgos; registra `CP-01 Drivers` y demuestra que `02`-`07` no conservan drivers críticos huérfanos o contradictorios. |
| `09` | Define un mapa común de capacidades/scopes incluidos y excluidos; compara configuraciones consolidada, híbrida o distribuida bajo los mismos drivers; declara cada opción bajo `### Alternativa <ID> — <Nombre>` y contiene dentro de cada sección un Mermaid lógico propio, compilable y comparable al mismo nivel de abstracción; no usa un diagrama compartido, draw.io o Excalidraw para reemplazar los Mermaid individuales; asigna cada scope a una unidad/forma desplegable con datos, comunicación y aislamiento lógico/de datos/recursos/fallos/despliegue; justifica tanto separación como agrupación y su condición de evolución; no trata Hexagonal/CQRS como alternativas macro ni convierte bounded contexts automáticamente en servicios; si Microfrontends puede cambiar la topología, compara SPA modular y alternativas UI con drivers, owners, composición, UX, rendimiento, seguridad, operación y rollback según su guía; formula recomendación explícita. Cada Mermaid sigue la notación de `guia-calidad-visual-diagramas.md` y supera `validate_mermaid.py --strict`, con compilación verificada o registrada como no verificada. |
| `10` | Registra selección humana, autoridad, fecha y estado `Seleccionada`; conserva/enlaza la matriz aprobada de asignación por alcance sin scopes incluidos pendientes; documenta condiciones y riesgos aceptados; la síntesis enlaza los `QA-xx` prioritarios con la estrategia elegida. |
| `10.1` | **Gate inicial:** identifica proyecto, `ARQ-xxx`, estado, versión, owner/fecha; define el propósito de los arquetipos y cubre cada scope; inventaría cada scaffold requerido y contiene una ficha por arquetipo implementable con scopes, características, árbol de carpetas o N/A justificado, patrones/controles, comandos confirmados o abiertos con owner, configuración sin secretos, diferencias/reutilización y aceptación; documenta componentes compartidos, convenciones transversales, relación con legado, prioridad/dependencias y decisiones de framework; cada tecnología tiene baseline, uso, scope, estado, hosting, owner y evidencia/decisión; pilotos tienen acción/responsable hacia `11`-`13`; coincide con `10`; si aplica Microfrontends registra subarquetipo, shell, unidades, composición, baseline, owners, capacidad de entrega y hosting, con enlace a pipeline AS-IS/Vulcano cuando exista; permite `CT/enlace Pendiente de diseño` con owner; usa `05.04.06-Analysis-Archetypes.md` solo como ejemplo estructural y no copia sus decisiones. **En `25`:** actualiza `CT-xx`/enlaces, resuelve tecnologías abiertas y comprueba coincidencia con `14`, `14.00`, `16`, `17`, `18`, `19.1` cuando aplique, `20` y `21`; en B exige evidencia y en C separa AS-IS/TO-BE. |
| `11` | Cada tecnología evaluada tiene evidencia sobre madurez, soporte, seguridad, operación y salida; termina en `Adoptar`, `Pilotear` o `Descartar`; todo piloto se enlaza con `10.1`, `12` y, si aplica, `13`; actualiza el baseline tecnológico. |
| `12` | Cada incertidumbre registra componente, hipótesis, impacto, confianza, método, umbral, responsable y estado; toda incertidumbre crítica queda resuelta, aceptada explícitamente o enviada a `13`; si `13` no aplica, registra `CP-02 Selección y viabilidad` y la reconciliación `09`-`12`/`10.1`. |
| `13` | Define hipótesis y umbrales antes de ejecutar; conserva evidencia reproducible; compara métricas con umbrales; registra decisión; no deja una incertidumbre crítica indeterminada; registra `CP-02 Selección y viabilidad` cuando existe PoC y actualiza los artefactos afectados. |
| `14` | Materializa la matriz seleccionada en `10` y el baseline de `10.1`; clasifica todos los `CT-xx`; el C4 Nivel 2 coincide con el inventario; actualiza los `CT-xx` del arquetipo; enlaza `14.00` cuando existan interfaces programáticas; enlaza un `14.xx` por contenedor significativo y un `16.xx` cuando corresponde; en Microfrontends modela como contenedor solo unidades construibles/versionables/desplegables independientemente y deja módulos conjuntos como componentes; justifica desviaciones; si `17` no aplica, registra aquí `CP-03 Integridad del diseño`. |
| `14.00` | Declara alcance, protocolos, baseline y reglas de nomenclatura/compatibilidad; cada `API-xxx` y `API-xxx-OP-xxx` tiene ID estable, propósito, owner `CT-xx`/`EXT-xx`, consumidor, exposición, seguridad, estado y contrato/evidencia; las operaciones se trazan a `FAS/QA` u otro driver, secuencias y decisiones; las operaciones críticas cubren errores, idempotencia/concurrencia, datos, límites y SLO aplicables; los contratos propios requeridos existen bajo el `14.xx` owner y los externos enlazan su fuente autoritativa o snapshot no canónico, validan y coinciden con el catálogo; no hay contratos sin owner, duplicados ni breaking changes sin disposición; en B aporta evidencia reproducible y en C documenta compatibilidad/transición. |
| `14.xx` | Incluye C4 Nivel 3, responsabilidades, componentes y contratos; referencia los `API-xxx`/`API-xxx-OP-xxx` que publica o consume y aplica las reglas de `14.00`; genera/enlaza contratos ejecutables requeridos sin duplicarlos en Markdown; traza `QA-xx`/`FAS-xxx`; evalúa Hexagonal/Capas y patrones de diseño dentro del scope con problema, alternativa y validación; evalúa CQRS solo para sus comandos/lecturas; si es shell/microfrontend cubre rutas, composición/versionado, estado, UX, seguridad, dependencias, rendimiento, fallos, telemetría, capacidad de entrega independiente y rollback, con enlace a pipeline AS-IS/Vulcano cuando exista; aplica o justifica `CC-xxx`; cubre seguridad, resiliencia y observabilidad; enlaza datos, decisiones y riesgos del `CT-xx`. |
| `15` | Cubre todos los flujos críticos; incluye rutas de error y asincronía relevantes; participantes, `API-xxx-OP-xxx` y contratos coinciden con `14.00`/`14.xx`; para Microfrontends cubre bootstrap/autorización, navegación/comunicación y remote incompatible/no disponible; enlaza `FAS-xxx` y decisiones aplicables. |
| `16` | Cataloga cada conjunto persistente relevante con `DATA-xxx`, owner, fuente de verdad, store, sensibilidad, retención/borrado, modelo dueño y estado; evita ownership ambiguo; documenta flujos, duplicación controlada y consistencia; enlaza todos los `16.xx` aplicables. |
| `16.xx` | Declara el tipo de motor elegido y su justificación siguiendo `references/guia-catalogo-bases-de-datos.md` (matriz de `references/guia-matriz-decision.md` si hubo 2+ alternativas viables); declara objetivo de entrega y madurez conceptual/lógica/física; incluye matriz de cobertura `driver → API/OP/evento → schema → DATA → entidad → estructura/store → operación → clasificación/retención`; demuestra que toda persistencia narrada en otros artefactos está modelada; declara fuente de verdad y modelo del `CT-xx`; documenta transacciones, concurrencia y consistencia; si usa CQRS, documenta comandos, escritura, proyecciones, lag, reconstrucción y operación, y si no lo usa evita estructuras artificiales; cubre seguridad/PII, retención, migración, recuperación y trazabilidad; si existe nivel físico incluye `## Diccionario físico de datos` según `references/guia-diccionario-fisico-datos.md`; si el objetivo es listo para implementación enlaza un `16.xx.y` procesable validado, documenta el 100 % de sus objetos/campos y registra migración/rollback. |
| `16.xx.y` | Declara formato/dialecto y versión; contiene tablas/colecciones/campos/tipos, claves/referencias, nulabilidad, restricciones, índices y particiones aplicables; coincide con `DATA-xxx`, contratos, `16.xx` y su diccionario físico 1:1; registra validación procesable y estrategia de migración/rollback; no contiene secretos ni datos sensibles reales. |
| `17` | Mapea cada contenedor lógico a despliegue; tecnologías/servicios y hosting coinciden con `10.1`; documenta ambientes y topología; identifica patrones cloud y valida alcance, fallos, seguridad, operación, costo y lock-in; para Microfrontends cubre hosting/CDN, caché, CSP/integridad, compatibilidad, capacidad de despliegue autónoma, telemetría y rollback por unidad, con enlace a pipeline AS-IS/Vulcano cuando exista; enlaza/evalúa `17.1`-`17.5`; registra `CP-03 Integridad del diseño` con cero capacidades perdidas o elementos críticos huérfanos. |
| `17.1`/`17.2`/`17.3` | El `.drawio` usa XML sin compresión, una página y un solo proveedor; cada recurso cloud declara `archiIconId` activo y coherente con `catalogo_iconos_curado.json`, o una excepción aprobada y registrada; no contiene placeholders `[CT-*]`, bibliotecas legadas ni mezcla de proveedor; supera `validate_drawio_catalog.py --strict`; componentes, relaciones, límites, protocolos y nombres coinciden con C4, `10.1`, `17`, decisiones e IaC; muestra zonas, escalado, seguridad, observabilidad y puntos de fallo relevantes; registra fecha, SHA-256, `catalogVersion`, commit fuente y resultado. Supera además `validate_drawio_layout.py --strict`: conectores ortogonales y etiquetados sin atravesar nodos, sin solapamientos ni desbordes de contenedor, íconos uniformes y leyenda. |
| `17.4` | Declara proveedor, región, modalidad, fecha, moneda, fuentes y clasificación de evidencia (pública/contractual/observada/aproximada); dimensionamiento trazable por ambiente; cubre inventario de `17` y partidas de `17.4.1`, exclusiones y recursos compartidos; separa mensual/único y escenarios; bloques `17.4`/`17.5` generados y verificados con `validate_pricing.py`; revisión comercial documentada aparte del chequeo aritmético. Si hay IA, incluye generación, embeddings, cargos adicionales y alternativas de modelo sin doble conteo. Pricing histórico sin manifiesto tiene brecha explícita, no cierre validado bajo este contrato. |
| `17.6` | Cumple los criterios de cierre de `references/guia-infraestructura-cloud.md` §11; cada `CT-xx` de `17` queda ubicado en cuenta y red; los `.drawio` `17.6.N` superan ambos validadores estrictos. |
| `17.7` | Cumple los criterios de cierre de `references/guia-diagrama-a-iac.md` §13; `17.7.1` reproducible con `extract_drawio_inventory.py` y hash de cada fuente; esqueleto, si existe, con validación registrada. |
| `17.5` | El HTML renderiza sin errores; sus diagramas coinciden con `17.1`-`17.3`; sus cifras coinciden exactamente con `17.4`, incluido el rango de IA/LLM cuando aplique; muestra supuestos y recomendación. |
| `18` | Cada `QA-xx` prioritario tiene `TP-xxx` o justificación en la matriz de cobertura; clasifica y cubre explícitamente táctica arquitectónica, patrón arquitectónico, patrón de diseño, patrón cloud y patrón IA con estado o motivo; cada `TP-xxx` tiene tipo, estado, owner, parámetros, `CT-xx`, `DA-xxx` o motivo para no requerirla, mecanismo, fallos, trade-offs, operación, validación específica del tipo y evidencia; si Microfrontends aplica, valida autonomía, composición, compatibilidad, performance, seguridad, UX, operación y rollback; incluye todas las tácticas/patrones aplicados aunque tengan decisión en `20`; los Mermaid requeridos aportan información, compilan y no duplican `15`; no incluye patrones genéricos sin uso. |
| `19` | Incluye todas las subsecciones obligatorias o `Missing evidence`; evalúa los patrones IA aplicables con datos, modelo, guardrails, observabilidad, costo y fallback; contiene la matriz `CC-xxx` con regla, alcance, automatización, umbral, evidencia de definición, evidencia de ejecución, responsable y estado/excepción; en Caso C separa estado AS-IS y TO-BE; los aspectos transversales son consistentes con `14.xx`, `16.xx`, despliegue y decisiones. |
| `19.1` | Declara alcance, fuentes, método y escala; identifica activos, datos, superficies y fronteras de confianza; cada amenaza prioritaria `THR-xxx` tiene actor, escenario, riesgo y disposición; cada amenaza material enlaza `SEC-xxx` o aceptación autorizada; cada `SEC-xxx` tiene alcance, criterio observable, clase de evidencia, owner y estado; traza `THR → SEC → CT/API/OP/DA/TP → validación`; envía riesgos residuales a `21` y decisiones/excepciones a `20`; entrega a Vulcano todos los `SEC-xxx` aplicables sin prescribir herramientas ni pipeline; en B/C separa intención, evidencia y transición. |
| `20` | Cada `DA-xxx` tiene estado, contexto, alternativas, consecuencias y validación; no hay IDs duplicados; conserva la historia de decisiones reemplazadas; coincide con el diseño vigente; después de `21`-`22` o `24` registra `CP-04 Reconciliación`, actualiza decisiones vivas y deja cero contradicciones activas o riesgos críticos sin disposición. |
| `21` | Cada riesgo tiene impacto, probabilidad, mitigación, responsable y disparador; los riesgos críticos enlazan `QA-xx`, `CT-xx`, PoC o `DA-xxx`; la deuda tiene disposición. |
| `22` | Define términos y siglas no evidentes; no contradice el lenguaje del dominio ni otros artefactos; usa una denominación única por concepto. |
| `23` | Cada brecha AS-IS/TO-BE identifica `CT-xx` o capacidad afectada, esfuerzo y riesgo; cubre todas las decisiones TO-BE que requieren cambio. |
| `24` | Las fases producen estados operables; explicita dependencias, validación y rollback; asigna cada brecha de `23`; identifica hitos, responsables o condiciones de avance. |
| `25` | Audita los criterios de todos los artefactos aplicables `01`-`24` y assets contra un snapshot con SHA-256; incluye cada compromiso/driver aplicable en la matriz `prometido → respuesta → evidencia → estado` y cada `ARQ/CT/API/TP` material en trazabilidad inversa hacia su driver/decisión; distingue `Definido/Diseñado/Verificado/Demostrado/Implementado/Validado` según escenario; verifica correspondencia `10 → 10.1 → 14/14.00/16/17`, scopes, tecnologías, contratos, datos, despliegue, costos, tácticas, `CC-xxx`, `THR → SEC` y handoff; registra `CON-xxx`, huérfanos e indicadores; ejecuta ATAM y `validate_architecture_coherence.py --strict`; su dictamen es `Apto`/`Apto con observaciones` solo con cero bloqueantes, cero contradicciones críticas/altas abiertas y todos los compromisos críticos cubiertos; asigna responsable/fecha a observaciones. |
| `25.1` | El manifiesto cumple el esquema; el HTML ofrece vistas Ejecutiva/Arquitectura/Completa y funciona sin red; explicita decisión solicitada, valor, costo/plazo o faltantes, evidencia del trabajo, drivers, alternativas, selección, diseño por contenedor, datos, cloud, tácticas, amenazas/requisitos `SEC-xxx` materiales cuando apliquen, decisiones, ATAM, riesgos y roadmap; cada afirmación material enlaza fuente/hash; diagramas locales son legibles; faltantes y contradicciones están visibles; si no es apta muestra el watermark; pasa `validate_architecture_presentation.py`. |
| `26` | Identifica participantes y versiones revisadas; contiene decisión humana explícita; registra observaciones, condiciones y compromisos con responsable; el agente no se autoaprueba. |

## Artefactos complementarios de despliegue

`17-Vista-de-Despliegue.md` es el único punto de entrada para:

- `17.1-Despliegue_AWS_<Proyecto>.drawio`
- `17.2-Despliegue_Azure_<Proyecto>.drawio`
- `17.3-Despliegue_GCP_<Proyecto>.drawio`
- `17.4-Pricing_<Proyecto>.md`
- `17.5-Arquitectura_Costos_<Proyecto>.html`

Omite los proveedores que no apliquen y conserva el número fijo de cada tipo. Los assets no documentales heredan el prefijo del archivo dueño.

## Artefactos complementarios de presentación

`25.1.1-Manifiesto-Presentacion_<Proyecto>.json` es la entrada estructurada de `25.1-Presentacion-Comite-Arquitectura_<Proyecto>.html`. Las exportaciones locales de diagramas usan `25.1.2-*`, `25.1.3-*`, etc.; conservan enlace y hash del diagrama/documento canónico. La presentación es derivada y nunca sustituye `05`, `09`, `10`, `10.1`, `14`-`21` ni `25`.

## Gobierno y catálogo de APIs (`14.00`)

Sigue `references/guia-gobierno-y-diseno-apis.md`. Reserva `14.00` para el documento transversal y nunca lo asignes a `CT-00`. Genera su borrador después de identificar los contenedores en `14`, consolídalo desde cada `14.xx` y ciérralo antes de `15`.

`14.00` contiene las reglas adoptadas y el catálogo canónico, no los esquemas completos. Asigna `API-001`, `API-002`, etc. y operaciones estables `API-001-OP-001`; conserva IDs retirados sin reutilizarlos. Los contratos ejecutables pertenecen al `14.xx` del contenedor owner y heredan su prefijo, por ejemplo `14.03.1-OpenAPI_API-001_Nomina.yaml`. Para otros protocolos usa AsyncAPI, `.proto`, GraphQL SDL o el formato aprobado, sin generar variantes que no apliquen.

Una API se delimita por capacidad, consumidores, ownership, seguridad y ciclo de vida; no se crea automáticamente una por microservicio, frontend o repositorio. En el catálogo usa “operación” para el contrato consumible y agrega `Handler/Función` solo como mapeo opcional cuando exista implementación serverless.

## Diseño detallado por contenedor (`14.xx`/`16.xx`)

Sigue `references/guia-diseno-detallado-contenedores.md`. Asigna IDs estables `CT-01`, `CT-02`, etc. en el orden de declaración del C4 Nivel 2 y reutiliza el mismo sufijo: `14.01` y `16.01` pertenecen siempre a `CT-01`. Agrega contenedores nuevos al final sin renumerar los existentes.

`14-Vistas-C4.md` contiene la vista global y demuestra que todos los contenedores fueron clasificados. Cada contenedor significativo tiene un `14.xx`. Cada `14.xx` referencia las APIs/operaciones que publica o consume, posee sus contratos ejecutables propios y enlaza la fuente autoritativa o snapshot no canónico de contratos externos; `14.00` consolida el catálogo sin duplicarlos. Cada contenedor significativo con datos persistentes o estado no trivial tiene además un `16.xx`; si no aplica, la matriz de cobertura registra la razón. Un frontend puede ser significativo y puede requerir modelo de estado igual que un microservicio.

## Subsecciones obligatorias de `19-Dimensiones-Arquitectonicas.md`

Incluye siempre estas subsecciones; si falta evidencia escribe `Missing evidence`:

1. Integraciones.
2. Datos y analítica.
3. IA y patrones de IA, si aplica; evalúa RAG, Context Engineering, Fine-tuning, Agent Pattern u otros del catálogo únicamente cuando respondan a una necesidad y registra datos, modelo, evaluación, guardrails, observabilidad, costo y fallback.
4. Seguridad.
5. Calidad interna, pruebas y Clean Code; define la matriz `CC-xxx` siguiendo `references/guia-clean-code.md` y enlaza su aplicación por `CT-xx` en `14.xx`.
6. Observabilidad y operación.
7. UX, accesibilidad e internacionalización.
8. Low-code/No-code, si aplica.

La subsección Seguridad resume drivers, alcance y decisiones transversales. Si se activa `19.1`,
enlaza el documento especializado y no duplica su catálogo `THR-xxx`/`SEC-xxx`. Si no se
activa, registra el análisis de no aplicabilidad y la condición que obligaría a reevaluarlo.

## Modelo de amenazas y requisitos de seguridad (`19.1`)

Sigue `references/guia-modelo-amenazas-y-requisitos-seguridad.md`. `19.1` es condicional, pero
la evaluación de aplicabilidad es obligatoria. Es dueño de `THR-xxx`, `SEC-xxx`, trust
boundaries, escenarios de abuso, criterios de aceptación y riesgo residual de seguridad.

`archi` define **qué propiedad debe cumplir el sistema** y cómo se acepta arquitectónicamente.
Vulcano define **cómo se operacionaliza y evidencia continuamente**: scanners, pipeline,
severidades, SLA, SBOM, firma/provenance, policy as code y gestión operativa de secretos. En
greenfield, un `SEC-xxx` completo puede quedar `Definido`; la ausencia de pipeline no impide
cerrar la arquitectura si el handoff está listo y no se afirma implementación inexistente.

## Escenario de calidad completo (`05`)

`05-Atributos-de-Calidad.md` inicia con esta tabla. En A/C se crea como borrador con los escenarios candidatos y `Pendiente de QAW` en orden/prioridad; se reemplaza con el resultado acordado en `07`. En B se ordena según evidencia AS-IS. La versión cerrada incluye una fila por escenario priorizado, aunque varios pertenezcan al mismo atributo:

```markdown
## Resumen de atributos y escenarios priorizados
| Orden | Atributo principal | Escenario | Objetivo de negocio | Prioridad / Votos o ranking | Justificación |
|---:|---|---|---|---|---|
| 1 | Disponibilidad | QA-01 | [OBJ-02](02-Contexto-y-Alcance.md#objetivos-de-negocio) | Alta / 8 votos | Operación 24×7 |
```

Cada `QA-xx` sigue el formato largo SEI (Bass/Clements/Kazman), ampliado con la trazabilidad y los campos de trabajo del formato `GRCpl101_AtributosCalidad`:

```markdown
#### QA-01: [Nombre corto del escenario]
- **Descripción del escenario:** [resumen inequívoco de la situación y resultado esperado]
- **Objetivos de negocio:** [OBJ-01](02-Contexto-y-Alcance.md#objetivos-de-negocio) [agrega al menos un enlace `OBJ-xx`]
- **Atributos de calidad relevantes:** [atributo principal; atributos secundarios afectados]
- **Fuente del estímulo:** [quién/qué origina el estímulo — usuario, sistema externo, carga, fallo]
- **Estímulo:** [la condición que llega al sistema]
- **Entorno:** [en qué circunstancia ocurre — operación normal, sobrecarga, arranque, degradado]
- **Artefacto:** [qué parte del sistema recibe el estímulo, si ya se conoce]
- **Respuesta:** [qué debe hacer el sistema]
- **Medida de la respuesta:** [métrica verificable — tiempo, tasa, %, etc.]
- **Prioridad:** [alta/media/baja o el resultado de la votación de `07`]
- **Validación:** [cómo se comprobará — prueba, PoC, monitoreo en producción]
- **Preguntas pendientes:** [preguntas, cada una con responsable/disposición; o `Sin preguntas pendientes`]
- **Problemas detectados:** [problemas, cada uno enlazado a supuesto/riesgo/decisión y responsable; o `Sin problemas detectados`]
```

No inventes un `OBJ-xx`: debe existir y estar definido en `02`. Si falta, registra `Missing evidence` en `Preguntas pendientes` y deja `05` en `No cumple` hasta resolverlo. Para escenarios de prioridad baja o donde Fuente/Entorno sean obvios y no aporten (ej. "cualquier usuario, en cualquier momento"), puedes simplificar su contenido, pero conserva todos los campos y escribe el valor explícito; no omitas líneas. Los escenarios priorizados siempre requieren contenido completo.

## Cobertura de atributos de calidad (`07`)

`07-Resultado-QAW.md` incluye esta matriz recorriendo los 13 atributos de `references/guia-catalogo-tacticas-calidad.md` — ninguno queda fuera de la tabla y Seguridad siempre tiene fila:

```markdown
### Cobertura de atributos de calidad
| Atributo | Estado | `QA-xx` / Motivo |
|---|---|---|
| Disponibilidad | Priorizado | QA-02 |
| Rendimiento | Priorizado | QA-05 |
| Seguridad | Priorizado | QA-03 |
| Portabilidad | Considerado y descartado | No hay requisito multi-plataforma en este proyecto |
| Interoperabilidad | No aplica | Sistema sin integraciones externas previstas |
| ... | ... | ... |
```

Estados posibles: **Priorizado** (tiene `QA-xx` propio), **Considerado y descartado** (se discutió pero no amerita un escenario dedicado — indica el motivo), **No aplica** (no tiene sentido para este sistema — indica el motivo). No se permite omitir un atributo de la tabla.

## Cobertura de pilares Well-Architected (`08`)

`08-Well-Architected.md` incluye esta matriz recorriendo los 6 pilares de `references/guia-well-architected.md`. A diferencia de `07`, esta cobertura es holística: no depende de que un `QA-xx` haya priorizado el pilar.

```markdown
### Cobertura de pilares Well-Architected
| Pilar | Estado | `PD-xx`/`BP-xxx` / Motivo |
|---|---|---|
| Excelencia Operacional | Cubierto | PD-01, BP-003 |
| Seguridad | Cubierto | PD-02 |
| Confiabilidad | Cubierto | PD-03 (deriva de QA-02) |
| Eficiencia de Rendimiento | Cubierto | PD-04 (deriva de QA-05) |
| Optimización de Costos | Considerado y descartado | Volumen bajo; se revisará en la primera iteración post-lanzamiento |
| Sostenibilidad | No aplica | Carga interna, bajo volumen, sin objetivo de sostenibilidad del cliente |
```

Estados posibles: **Cubierto**, **Considerado y descartado** (se evaluó pero no amerita prácticas adicionales — indica el motivo), **No aplica** (con motivo concreto; Seguridad y Confiabilidad rara vez califican aquí). Ningún pilar queda fuera de la tabla.

## Compromisos y lecciones aprendidas (`07`, `25`, `26`)

Cualquier artefacto que documente una reunión de gobierno (QAW, revisión técnica, validación/aprobación) cierra con estas dos tablas:

```markdown
### Compromisos
| ID | Descripción | Responsable | Seguimiento | Fecha propuesta de cierre |
|---|---|---|---|---|
| C-01 | [qué se comprometió a hacer] | [nombre/rol] | [cómo se hará seguimiento] | [fecha] |

### Lecciones aprendidas
| ¿Hubo lecciones aprendidas? | Descripción |
|---|---|
| Sí/No | [si sí, qué se aprendió y qué se haría distinto la próxima vez] |
```

Si no hubo compromisos o lecciones en una sesión puntual, dilo explícitamente ("Sin compromisos pendientes" / "No"), no omitas la sección.

## Auditoría de coherencia (`25`)

Sigue `references/guia-auditoria-coherencia-arquitectura.md`. Además de la matriz de criterios de cierre, `25` contiene obligatoriamente y con esos encabezados:

1. `Snapshot de artefactos auditados`, con versión/SHA-256.
2. `Matriz de compromisos arquitectónicos`, que compara promesa, criterio, respuesta, evidencia y estado.
3. `Trazabilidad bidireccional de elementos de diseño`, que justifica cada elemento material desde un driver/restricción/decisión.
4. `Registro de contradicciones y elementos huérfanos`, con IDs `CON-xxx`.
5. `Indicadores de cobertura`, sin usar promedios para compensar bloqueantes.
6. ATAM por `QA-xx` prioritario.
7. `Dictamen de auditoría` y salida de `validate_architecture_coherence.py --strict`.

El dictamen `Apto` corresponde a cierre `Cumple`; `Apto con observaciones`, a `Cumple con observaciones`; `No apto`, a `No cumple`. Si cambia una fuente, actualiza el snapshot y repite la auditoría completa.

## Análisis ATAM por escenario (`25`)

`25-Revision-Tecnica-Arquitectura.md` incluye esta tabla por cada `QA-xx` priorizado, evaluando la arquitectura **ya diseñada** en `14`-`19` (no la propuesta en abstracto de `09`):

```markdown
#### Análisis ATAM — QA-01
| Campo | Detalle |
|---|---|
| Enfoque arquitectónico | [qué parte del diseño responde a este escenario] |
| Decisiones que lo soportan | [`DA-xxx` relevantes] |
| Punto de sensibilidad | [qué parámetro del diseño, si cambia, afecta directamente este atributo] |
| Punto de equilibrio (trade-off) | [qué otro atributo se sacrifica o se limita por esta decisión] |
| Riesgo | [qué podría fallar; enlaza a `21` si ya está registrado] |
| Razonamiento | [por qué el equipo considera que el diseño satisface el escenario] |
```

Este análisis es lo que diferencia una revisión de completitud de una revisión ATAM real. Evalúa también los `14.xx`/`16.xx` que implementan cada escenario. Si un `QA-xx` crítico no tiene análisis o no puede trazarse a un contenedor, es un hallazgo bloqueante de `25`.

## Objetivos de negocio, interesados y contexto técnico (`02`)

`02-Contexto-y-Alcance.md` incluye, además del C4 Contexto, estas tres tablas. Los `OBJ-xx` son estables y constituyen el destino de trazabilidad de `05`:

```markdown
### Objetivos de negocio
| ID | Objetivo | Medida de éxito | Fuente / Responsable |
|---|---|---|---|
| OBJ-01 | [resultado de negocio esperado] | [indicador y objetivo medible] | [stakeholder o fuente] |

### Interesados
| Rol / Nombre | Contacto | Expectativas |
|---|---|---|
| [Rol/Nombre] | [canal de contacto] | [qué espera de la arquitectura o su documentación] |

### Contexto técnico
| Sistema externo | Protocolo / Canal | Dirección del dato |
|---|---|---|
| [nombre del sistema o partner] | [REST/HTTPS, SFTP, cola, etc.] | [entrante/saliente/bidireccional] |
```

Usa la tabla de objetivos para trazar cada `QA-xx` y `FAS-xxx` al valor esperado. Usa la tabla de interesados para decidir a quién convocar en el QAW (`07`) y en la validación (`26`). La tabla de contexto técnico complementa el C4 Contexto (que muestra *con quién* interactúa el sistema) explicitando *cómo* — protocolo y dirección — sin repetir el detalle de infraestructura productiva que vive en `17`.

## Síntesis de estrategia de solución (`10`)

`10-Seleccion-de-Arquitectura.md` cierra con una síntesis breve (3-6 líneas, no una tabla exhaustiva) que conecta los `QA-xx` prioritarios con el enfoque elegido:

```markdown
### Síntesis de estrategia de solución
- **`QA-02` (disponibilidad):** resuelto con [enfoque/patrón], ver `09`/`20`.
- **`QA-05` (rendimiento):** resuelto con [enfoque/patrón], ver `09`/`20`.
- **`QA-xx` (...):** ...
```

Esta síntesis no reemplaza la comparación detallada de `09` ni las decisiones de `20`: es el resumen "de un vistazo" que permite a un lector nuevo entender en segundos por qué se eligió la alternativa, antes de profundizar en el detalle.

Antes de la síntesis, incluye o enlaza la matriz aprobada de `09`:

```markdown
### Configuración seleccionada por alcance
| Capacidad / scope | `FAS/QA` | Unidad desplegable / Agrupación | Forma y aislamiento | Datos/consistencia | Comunicación | Driver de separación/agrupación | Condición de evolución |
|---|---|---|---|---|---|---|---|
```

Cada capacidad incluida tiene una fila. Esta tabla es el contrato que `14-Vistas-C4.md` materializa; cualquier desviación posterior requiere actualizar `10` o registrar una `DA-xxx` aprobada.

## Arquetipo de solución y baseline tecnológico (`10.1`)

Sigue `references/guia-arquetipo-solucion.md`. `10.1` es el perfil técnico canónico y vivo del proyecto: clasifica `ARQ-xxx`, cubre cada scope de `10`, registra tecnologías/versiones/estados/owners/evidencia y enlaza el detalle de `14`-`21`. En Caso B usa estado `Observado`; en C separa `AS-IS → TO-BE`.

Registra por separado `Estado del arquetipo` (`Propuesto/Seleccionado/Observado/Validado/Obsoleto`) y `Estado de cierre del artefacto` (`Cumple/Cumple con observaciones/No cumple/No aplica`). Una selección aprobada no demuestra completitud documental.

El inventario de tecnologías de `10.1` es dueño del baseline seleccionado u observado. `14`/`16`/`17` explican su aplicación y deben coincidir; `11`-`13` gobiernan cualquier elemento `Pilotear`. No copies diagramas, contratos, fichas `TP-xxx` ni decisiones completas dentro del arquetipo.

## Ficha mínima e inventario de building blocks (`14`)

Para cada contenedor o componente no trivial agrega esta ficha en `14` o en su `14.xx`:

```markdown
#### [Nombre del bloque]
- **Responsabilidad:** [qué hace, en una frase]
- **Satisface:** [`QA-xx`, `FAS-xxx` relevantes]
- **Problemas abiertos:** [si aplica; si no, omite la línea]
```

Además, `14-Vistas-C4.md` incluye la matriz de cobertura definida en `references/guia-diseno-detallado-contenedores.md`; la ficha no reemplaza el diseño `14.xx` de un contenedor significativo.

## Ciclo de vida de decisiones (`20`)

Cada entrada `DA-xxx` de `20-Decisiones-Arquitectonicas.md` incluye un campo **Estado**, con estos valores:

| Estado | Cuándo usarlo |
|---|---|
| `Propuesta` | La decisión está documentada pero aún no confirmada por la autoridad correspondiente |
| `Aceptada` | Confirmada y vigente |
| `Obsoleta` | Ya no aplica, pero no fue reemplazada por una decisión puntual (ej. el driver que la motivó desapareció) |
| `Reemplazada por DA-xxx` | Otra decisión la sustituyó explícitamente; enlaza al `DA-xxx` sucesor |

En Caso C, revisa el estado de cada `DA-xxx` heredado del AS-IS: las que el TO-BE reemplaza deben quedar `Reemplazada por DA-xxx`, no eliminadas ni dejadas como `Aceptada` por omisión.

## Contenido del orquestador

```markdown
# Documento de Arquitectura: [Proyecto]

**Versión:** [x] · **Fecha:** [fecha] · **Tipo:** [Propuesta/AS-IS/TO-BE]
**Estado:** [Aprobada/Aprobada con condiciones]

## Propósito
[2-4 líneas]

## Resumen ejecutivo
[Alternativa seleccionada, razones y condiciones abiertas. Enlaces a 09, 10 y 26.]

## Interesados
[Quién usa, opera, selecciona y aprueba.]

## Índice
| # | Documento | Contenido |
|---|---|---|
| 01 | [Línea Base](01-Linea-Base_<Proyecto>.md) | ... |
| 02 | [Contexto y Alcance](02-Contexto-y-Alcance.md) | ... |
| ... | ... | ... |
```

## Reglas de propiedad y trazabilidad

1. Un tema tiene un solo archivo dueño; otros archivos citan su ID y enlazan.
2. Usa solo estos esquemas: `OBJ-xx`, `RT-Dxx`/`RN-Dxx`/`RR-Dxx`, `SUP-Dxx`, `QA-xx`, `FAS-xxx`, `PD-xx`/`BP-xxx`, `ARQ-xxx`, `API-xxx`, `API-xxx-OP-xxx`, `API-xxx-ERR-xxx` cuando aplique, `DATA-xxx`, `THR-xxx`, `SEC-xxx`, `DA-xxx`, `TP-xxx`, `CC-xxx` y `CON-xxx` exclusivamente para contradicciones/huérfanos de `25`.
3. La comparación de configuración/nube vive en `09`; `10.1` posee el baseline tecnológico y composición de arquetipos; `20` contiene las decisiones y enlaza. Hexagonal/CQRS viven en decisiones separadas solo cuando su impacto lo amerita.
4. Las matrices de decisiones sin archivo propio viven en la entrada correspondiente de `20`.
5. Un diagrama tiene un solo dueño. No copies versiones completas en varios archivos.
6. `00` resume y enlaza; no desarrolla contenido.
7. En orden de generación, la trazabilidad mínima es `OBJ-xx → QA/FAS → 09 alternativa → 10 selección → 10.1 ARQ/tecnologías → CT-xx → 14/14.00 (API/OP) → 14.xx → 16/16.xx (DATA/modelo físico aplicable) → 15/17-19 (TP/CC) → 19.1 (THR/SEC, si aplica) → 20 decisiones → 25 revisión → 25.1 presentación trazable → 26 aprobación`. En `25` recorre también la dirección inversa: cada `ARQ/CT/API/DATA/TP`, tecnología crítica y servicio cloud material debe volver a un driver, restricción o `DA-xxx`.
8. Sigue `references/guia-diseno-detallado-contenedores.md` para clasificar y detallar contenedores.
9. Sigue `references/guia-gobierno-validacion.md` para QAW, selección, incertidumbres, PoC, revisión y aprobación.
10. Sigue `references/guia-gobierno-y-diseno-apis.md` para nomenclatura, catálogo, contratos ejecutables y ciclo de vida de APIs.
11. Sigue `references/guia-modelo-amenazas-y-requisitos-seguridad.md` para el análisis condicional de amenazas, requisitos `SEC-xxx` y handoff a Vulcano.
