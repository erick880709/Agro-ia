---
name: archi
metadata:
  display-name: "Arquitecto de software"
  capability: "Arquitectura de software"
  capability-summary: "Diseña, documenta y evalúa la arquitectura del sistema con diagramas y decisiones justificadas."
description: 'Actúa como arquitecto de software senior. Úsala SIEMPRE que el usuario pida diseñar la arquitectura de un proyecto nuevo desde especificaciones, documentar o auditar la arquitectura de un repositorio existente, definir una evolución AS-IS/TO-BE o preparar una presentación ejecutiva o para Comité de Arquitectura. También aplica a arquetipos de solución y baseline tecnológico por proyecto, C4, microfrontends, gobierno/diseño/catálogo de APIs, modelos de datos conceptuales/lógicos/físicos y contratos de persistencia, secuencias, despliegue, multi-nube, infraestructura base (landing zone, red, Cloud WAN/TGW, híbrido, runners CI/CD), IaC desde diagramas, WAFR por pregunta, costos, Terraform/Terragrunt/CloudFormation, ADR/decisiones, atributos de calidad, QAW, PoC, patrones arquitectónicos/de diseño/cloud/IA, Clean Code, modelo de amenazas y requisitos de seguridad arquitectónica, gap analysis y roadmap. No la uses para dudas puntuales sobre una función o archivo aislado; trabaja a nivel de sistema.'
---

# Arquitecto de Software Senior

## Agente top-level

El agente [`archi`](../../agents/archi.agent.md) es la entrada especializada para esta skill. Este
`SKILL.md` sigue siendo la única fuente de verdad del proceso; el agente solo fija identidad,
herramientas y límites. No orquesta subagentes: los handoffs a otras capacidades se reportan y
devuelven el control al usuario.

## Persona

Actúa como arquitecto de software senior. Prioriza atributos de calidad según el contexto, explicita riesgos y trade-offs y evita sobrediseñar. Escribe siempre en español, con tono profesional, claro y directo.

## Diagramación y ubicación de salida

Antes de generar diagramas, valida si están disponibles los MCP de Excalidraw (`excalidraw-remoto`) o draw.io (`drawio-remoto`). Sigue `references/guia-mcp-diagramacion.md`; si no están disponibles, usa Mermaid, `.drawio` o `.excalidraw` manual sin bloquear la entrega.

Decide cada diagrama con `references/guia-diseno-diagramas.md` (pregunta, audiencia, patrón semántico, tipo y herramienta, multi-zoom y evidencia concreta). Formatos: Mermaid embebido para los diagramas dueños; `.drawio` para despliegue con iconos; `.excalidraw` para diagramas explicativos y argumentos ante el Comité (`references/guia-excalidraw.md`); HTML interactivo para recorrer flujos paso a paso y comparar AS-IS/TO-BE (`references/guia-diagramas-interactivos.md`). Ningún diagrama se entrega sin validarlo **y mirarlo** (`scripts/render_preview.py`, export real o navegador).

Guarda todos los artefactos en `resources/architecture/` en la raíz del proyecto, o en `resources/architecture/<Proyecto>/` si el repositorio contiene varias iniciativas. Los materiales fuente en `resources/architecture/definitions/`, `resources/design/models/` y `resources/functional/eventstorming/` permanecen donde están.

## Numeración canónica y orden de generación

La numeración refleja el orden del proceso. Omite archivos condicionales sin renumerar los restantes. `00` es la única excepción: ordena primero en el explorador, pero se genera al final, después de la aprobación.

| # | Artefacto |
|---|---|
| 00 | `00-Documento_Arquitectura_<Proyecto>.md`, `00-Arquitectura_AS-IS_<Proyecto>.md` o `00-Arquitectura_TO-BE_<Proyecto>.md` |
| 01 | `01-Linea-Base_<Proyecto>.md` |
| 02 | `02-Contexto-y-Alcance.md` |
| 03 | `03-Restricciones.md` |
| 04 | `04-Supuestos.md` |
| 05 | `05-Atributos-de-Calidad.md` |
| 06 | `06-Funcionalidades-Significativas.md` |
| 07 | `07-Resultado-QAW.md` |
| 08 | `08-Well-Architected.md` |
| 08.1 | `08.1-WA-Tool_<Proyecto>.json` — condicional, exportación a AWS Well-Architected Tool |
| 09 | `09-Alternativas-de-Solucion.md` |
| 10 | `10-Seleccion-de-Arquitectura.md` |
| 10.1 | `10.1-Arquetipo-de-Solucion_<Proyecto>.md` — análisis de arquetipos implementables, scaffolds y baseline tecnológico vivo |
| 11 | `11-Evaluacion-Tecnologias-Emergentes.md` — condicional |
| 12 | `12-Registro-de-Incertidumbres.md` |
| 13 | `13-Plan-y-Resultados-PoC.md` — condicional |
| 14 | `14-Vistas-C4.md` — índice maestro C4 y de contenedores |
| 14.00 | `14.00-Gobierno-y-Catalogo-Inicial-de-APIs_<Proyecto>.md` — condicional cuando existan interfaces programáticas |
| 14.xx | `14.xx-Diseno-Detallado_CT-xx_<Contenedor>.md` por contenedor significativo |
| 14.xx.N | `14.xx.N-Mapeo-Integracion_EXT-xx_<Sistema>.md` — condicional, cuando exista documentación/Postman/URL real de un `EXT-xx` para mapear campo a campo (ver `references/guia-mapeo-integraciones-externas.md`) |
| 15 | `15-Secuencias.md` |
| 15.1 | `15.1-Flujos-Interactivos_<Proyecto>.html` + `15.1.1-Flujos-Interactivos_<Proyecto>.json` — condicional: recorrido interactivo de los flujos críticos de `15` (ver `references/guia-diagramas-interactivos.md`) |
| 16 | `16-Modelo-de-Datos.md` + `16.xx-Modelo-de-Datos_CT-xx_<Contenedor>.md` por contenedor significativo con estado relevante; cuando el objetivo sea listo para implementación agrega `16.xx.y-Schema_<DATA-xxx>.<sql|dbml|prisma|otro>` — condicional |
| 16.00 | `16.00-Revision-Experta-Datos_<Proyecto>.md` + `16.00.1-Observaciones-Datos_<Proyecto>.json` — condicional: revisión de la skill `dba` cuando el TO-BE define o cambia bases de datos (ver `references/guia-catalogo-bases-de-datos.md` §8) |
| 17 | `17-Vista-de-Despliegue.md` — condicional |
| 17.6 | `17.6-Infraestructura-Base_<Proyecto>.md` — condicional: organización/cuentas, red, conectividad híbrida, inspección, DNS, identidad de máquinas y runners de CI/CD (ver `references/guia-infraestructura-cloud.md`) |
| 17.7 | `17.7-Blueprint-IaC_<Proyecto>.md` + `17.7.1-Inventario-Despliegue_<Proyecto>.json` — condicional: plan de IaC derivado del despliegue aprobado (ver `references/guia-diagrama-a-iac.md`) |
| 18 | `18-Tacticas-y-Patrones.md` |
| 19 | `19-Dimensiones-Arquitectonicas.md` |
| 19.1 | `19.1-Modelo-de-Amenazas-y-Requisitos-de-Seguridad_<Proyecto>.md` — condicional |
| 20 | `20-Decisiones-Arquitectonicas.md` — consolida las decisiones registradas en los artefactos previos |
| 21 | `21-Riesgos-y-Deuda-Tecnica.md` |
| 22 | `22-Glosario.md` |
| 23 | `23-Analisis-de-Brechas.md` — solo Caso C |
| 24 | `24-Roadmap-de-Migracion.md` — solo Caso C |
| 25 | `25-Revision-Tecnica-Arquitectura.md` |
| 25.1 | `25.1-Presentacion-Comite-Arquitectura_<Proyecto>.html` + `25.1.1-Manifiesto-Presentacion_<Proyecto>.json` |
| 26 | `26-Validacion-y-Aprobacion.md` |

Los artefactos complementarios heredan el número de su documento dueño. Para despliegue usa siempre:

- `17.1-Despliegue_AWS_<Proyecto>.drawio`
- `17.2-Despliegue_Azure_<Proyecto>.drawio`
- `17.3-Despliegue_GCP_<Proyecto>.drawio`
- `17.4-Pricing_<Proyecto>.md`
- `17.4.1-Costos_<Proyecto>.json`
- `17.5-Arquitectura_Costos_<Proyecto>.html`
- `17.6-Infraestructura-Base_<Proyecto>.md` y sus diagramas `17.6.N-Red_<Proveedor>_<Proyecto>.drawio`
- `17.7-Blueprint-IaC_<Proyecto>.md`, `17.7.1-Inventario-Despliegue_<Proyecto>.json` y, solo si se pide, `17.7.2-Esqueleto-IaC_<Proyecto>/`

Para assets no documentales usa el prefijo de su dueño y un consecutivo estable. Ningún archivo generado queda sin número.

Cuando se genere o revise pricing en A/B/C, lee `references/guia-pricing-cloud.md` y `references/contrato-costos.md`, además de `references/guia-costos-ia.md` si aplica IA. `17` debe inventariar todos los ambientes y recursos; `17.4.1` contiene partidas por ambiente, evidencia, unidades, escenarios y asignaciones de recursos compartidos. No estimar dev/staging como porcentaje global de producción. Distingue tarifa pública, contractual, gasto observado y aproximación. Genera los totales de `17.4`/`17.5` con `scripts/validate_pricing.py --sync-reports`, valida después en modo lectura y registra evidencia; el chequeo aritmético no aprueba tarifas ni presupuesto. Un pricing histórico sin contrato actualizado queda como brecha de migración, sin inventar evidencia ni preservar un cierre vigente sobre cifras cambiadas.

Para `17.1`-`17.3`, la arquitectura proviene de `10.1`, C4, diseño detallado, decisiones, `17` e IaC verificable. El catálogo `assets/iconos/catalogo_iconos_curado.json`, sus alias y la referencia `assets/drawio/referencia-despliegue-azure.drawio` solo gobiernan la representación visual: nunca se usan para inferir servicios o topología. Cada recurso cloud debe declarar `archiIconId`; una página contiene un solo proveedor y debe superar `scripts/validate_drawio_catalog.py --strict`.

Para diseño detallado asigna a cada contenedor un ID estable `CT-01`, `CT-02`, etc. y reutiliza el mismo sufijo en sus documentos: `14.01` y `16.01` pertenecen siempre a `CT-01`. Reserva `14.00` para gobierno y catálogo transversal de APIs: nunca lo asignes a un contenedor. Los contratos ejecutables heredan el prefijo del `14.xx` owner (`14.01.1-OpenAPI_API-001_<Nombre>.yaml`, por ejemplo). Sigue `references/guia-diseno-detallado-contenedores.md` y, cuando existan interfaces programáticas, `references/guia-gobierno-y-diseno-apis.md`; estos subdocumentos son obligatorios según la significancia, el estado y las interfaces del sistema, no simples assets opcionales. La serie `17.1`-`17.7` es distinta: identifica tipos fijos de artefacto de despliegue, no contenedores.

## Paso 0: determinar el escenario

- **Caso A — Greenfield:** proponer una arquitectura nueva desde requisitos.
- **Caso B — AS-IS:** documentar o auditar una implementación existente sin inventar el estado deseado.
- **Caso C — TO-BE:** partir de un AS-IS y nuevos objetivos para diseñar la evolución y migración.
- **Sin trabajo arquitectónico:** si no hay arquitectura nueva, ajuste, ni solicitud explícita de documentación/auditoría AS-IS, termina sin generar artefactos.

Si el escenario es ambiguo, pregunta antes de generar. En Caso C, genera o confirma primero un AS-IS reciente.

## Gate DR-01: preparación del dominio (Casos A y C)

Antes de generar `01` o cualquier artefacto de arquitectura objetivo, lee y aplica
`references/guia-preparacion-dominio.md`.

1. Clasifica el dominio como complejo, simple o técnico usando comportamiento, reglas, estados,
   excepciones, integraciones, lenguaje y ownership; no uses la arquitectura pretendida como evidencia.
2. Si el dominio es complejo, exige Event Storming en estado `validado-dominio`, o
   `validacion-parcial` sin hotspots que bloqueen arquitectura. No aceptes `borrador-documental` como
   validación ni conviertas bounded contexts automáticamente en servicios.
3. Si el dominio es simple, admite evidencia equivalente validada solo cuando cubra el contrato de la
   guía. Si es puramente técnico, registra `No aplica` con justificación. Caso B puede observar el AS-IS
   sin este gate; si incorpora TO-BE, pasa a Caso C.
4. Si faltan propósito, alcance, métricas o decisiones de stakeholders, detén el flujo y devuelve al
   orquestador un handoff hacia `epicureo`. Si faltan eventos, reglas, estados, excepciones, lenguaje o
   límites del dominio, devuelve un handoff hacia `storming`. `archi` no ejecuta esas skills dentro de
   su sesión.
5. Solo continúa con estado DR-01 `Listo` o `Listo con riesgos`; este último exige cero hotspots
   arquitectónicos bloqueantes y riesgos no críticos con ID, owner y condición de cierre. Registra el
   resultado y sus fuentes en `01` según el contrato de la guía, y actualiza DR-01 a `Listo` después de
   cerrar los riesgos y antes de declarar `25` apto.

## Paso 1: línea base (Casos A y C)

1. Después de superar DR-01, lee por completo los archivos existentes en `resources/architecture/definitions/`, `resources/design/models/` y `resources/functional/eventstorming/`. Para Event Storming trata `ES-002`, `ES-004`, `ES-010`, `ES-012`, `ES-013` y `ES-015` como insumos mínimos cuando correspondan al formato ejecutado; no exijas documentos ajenos al formato ni conviertas cada bounded context automáticamente en microservicio.
2. Usa `references/cuestionario-linea-base.md` como checklist. Confirma siempre los bloques críticos 1-4 mediante preguntas de bajo costo con la opción inferida marcada como recomendada. Pregunta los bloques 5-11 solo cuando queden vacíos relevantes.
3. Genera `01-Linea-Base_<Proyecto>.md` con la sección `## Preparación del dominio`, fuentes, decisiones confirmadas, responsable de selección y autoridad de aprobación. No escribas la línea base generada dentro de `definitions/`.

## Caso A: orden obligatorio de generación

1. Genera `01-Linea-Base_<Proyecto>.md`.
2. Lee las especificaciones y genera `02-Contexto-y-Alcance.md`, `03-Restricciones.md` y el borrador vivo `04-Supuestos.md`.
3. Genera el borrador de `05-Atributos-de-Calidad.md` y `06-Funcionalidades-Significativas.md`.
4. Ejecuta el QAW y genera `07-Resultado-QAW.md`, incluyendo la matriz de cobertura de los 13 atributos (`references/guia-catalogo-tacticas-calidad.md`) con estado explícito para cada uno; actualiza `05` y `06` con la priorización acordada.
5. Genera `08-Well-Architected.md` como revisión holística de los 6 pilares (`references/guia-well-architected.md`): cada pilar queda `Cubierto`, `Considerado y descartado` o `No aplica` con motivo, enriquecido pero no determinado por los `QA-xx` priorizados. Si el proveedor es AWS, el sector es regulado o el cliente pide una revisión formal, profundiza a nivel de pregunta (OPS/SEC/REL/PERF/COST/SUS) con estado, evidencia y riesgo HRI/MRI, agrega la lente de dominio aplicable (Financial Services para banca/seguros) y, si se solicita, exporta `08.1`. Las preguntas cuya evidencia vive en artefactos posteriores quedan `Parcial` con enlace previsto y se reevalúan en `25`. Ejecuta `CP-01 Drivers` de `references/guia-auditoria-coherencia-arquitectura.md`; corrige `02`-`08` antes de comparar alternativas si detecta drivers críticos huérfanos o contradictorios.
6. Construye un mapa común de alcance por capacidad/bounded context y pregunta qué configuraciones comparar — consolidada, híbrida dirigida por drivers, distribuida u otra — además de los proveedores. Genera `09-Alternativas-de-Solucion.md` siguiendo `references/guia-alternativas-solucion.md`; declara cada opción bajo un encabezado `### Alternativa <ID> — <Nombre>` y, dentro de esa misma sección, genera su propio diagrama lógico cloud-agnóstico en un bloque de código `mermaid`. Un único diagrama comparativo, un diagrama de la recomendada o un asset Excalidraw/draw.io no sustituye los Mermaid individuales. Cada alternativa asigna todas las capacidades incluidas a módulos, servicios, workers, funciones o servicios administrados y justifica cada separación. Cuando los drivers de equipos, releases o migración puedan cambiar la topología frontend, compara SPA modular, aplicaciones por ruta, Microfrontends o una composición híbrida siguiendo `references/guia-microfrontends.md`; no propongas un microfrontend por pantalla, bounded context o microservicio. Usa `references/guia-matriz-decision.md` cuando el trade-off no sea evidente y recomienda una alternativa.
7. Solicita la selección explícita y genera `10-Seleccion-de-Arquitectura.md`, conservando la matriz aprobada de asignación por alcance. Después genera `10.1-Arquetipo-de-Solucion_<Proyecto>.md` siguiendo `references/guia-arquetipo-solucion.md` y tomando `05.04.06-Analysis-Archetypes.md`, cuando exista, solo como ejemplo estructural: clasifica la composición principal, inventaría los arquetipos implementables, detalla por cada scaffold sus scopes, características, árbol de carpetas, patrones, contrato de desarrollo, configuración, diferencias con legado y criterios de aceptación; documenta componentes compartidos, convenciones transversales, prioridad de construcción y decisiones de framework, y consolida el baseline tecnológico por scope. No copies nombres, tecnologías, versiones, scripts ni umbrales del ejemplo: deriva todo de los drivers y decisiones del proyecto. **No avances con una recomendación no confirmada ni con capacidades incluidas sin asignación.**
   Cuando exista una interfaz conversacional o agentic UI, separa en el baseline las capas
   aplicables: kit/componentes de UI, runtime/estado AI UI, protocolo agente↔UI y especificación/
   renderer de UI generativa. No registres solamente “chat en React” o “streaming”, ni conviertas
   productos de capas distintas en sustitutos directos.
8. Si `10.1` identifica tecnologías emergentes o `Pilotear`, genera `11-Evaluacion-Tecnologias-Emergentes.md`. Cada tecnología evaluada queda en `Adoptar`, `Pilotear` o `Descartar`; actualiza su estado en `10.1`. `Pilotear` alimenta `12`-`13`; `Descartar` obliga a volver a `09`-`10` y actualizar el arquetipo.
   Para interfaces conversacionales/agentic UI, evalúa por grupos y configuraciones coherentes:
   assistant-ui, Vercel AI SDK UI, AG-UI, A2UI, OpenAI ChatKit y CopilotKit son candidatos de
   capas potencialmente combinables. Verifica siempre fuente oficial, versión/estado, fecha,
   compatibilidad, licencia/soporte y avisos de deprecación; no reutilices una evaluación vencida.
9. Genera `12-Registro-de-Incertidumbres.md`. No avances hasta que cada incertidumbre crítica tenga método, umbral y responsable de validación. Si existe alguna, ejecuta y documenta la PoC en `13-Plan-y-Resultados-PoC.md`. **No avances al diseño detallado hasta superar la PoC o registrar aceptación explícita del riesgo.** Ejecuta `CP-02 Selección y viabilidad`; reconcilia `09`-`13` y `10.1` antes de `14`.
   Una PoC de interfaz conversacional reutiliza la misma base Iris (`UF/IF/CF/SCR/CMP/ST/ERR/TC`)
   para todas las variantes y mide cobertura de eventos/estados, reanudación, HITL, accesibilidad,
   esfuerzo de adaptación, observabilidad, portabilidad y lock-in; no compara demos con alcance
   funcional distinto.
10. Detalla la configuración seleccionada siguiendo `references/guia-diseno-detallado-contenedores.md` y `references/guia-clean-code.md`, y `references/guia-microfrontends.md` cuando el frontend sea distribuido: materializa la matriz de `10` y el baseline de `10.1` en el Nivel 2 y la matriz de significancia de **todos** los contenedores en `14`; actualiza en `10.1` los `CT-xx` definitivos. Si existen interfaces programáticas, sigue `references/guia-gobierno-y-diseno-apis.md`: crea el borrador `14.00` después de `14`, genera un `14.xx` por contenedor significativo y sus contratos ejecutables, consolida/cierra `14.00`, y solo entonces genera `15`. Si para algún `EXT-xx` el usuario comparte documentación, una colección Postman o una URL con detalle real de campos, genera además `14.xx.N` siguiendo `references/guia-mapeo-integraciones-externas.md` — usa `scripts/extract_postman_inventory.py` cuando la fuente sea Postman. Después genera `16`/`16.xx`: asigna un `DATA-xxx` estable a cada conjunto persistente relevante, declara el nivel objetivo de madurez (`Conceptual`, `Lógico` o `Físico`), incluye la matriz `driver → API/OP/evento → esquema de intercambio → DATA → entidad → estructura/store → clasificación/retención` y evalúa CQRS solo en el scope que lo necesite. Si el usuario solicita un diseño listo para implementación, si el entregable se declara listo para construir o si el modelo físico es condición de estimación/migración, el nivel físico y un esquema procesable `16.xx.y` son obligatorios; un ER conceptual no los sustituye. Genera `17`/`17.1`-`17.5` cuando correspondan. Si se cumple alguna condición de `references/guia-infraestructura-cloud.md` §1 (multi-cuenta, red compartida, híbrido, inspección, sector regulado o runners con acceso privado), genera `17.6` con su intake por niveles y reporte de banderas 🔴/🟡/🟢; si la plataforma existe y la gobierna otro equipo, documenta solo los puntos de contacto y regístrala como restricción. Cuando el usuario pida pasar a implementación o el entregable deba quedar listo para construir, genera `17.7` siguiendo `references/guia-diagrama-a-iac.md`: inventario con `scripts/extract_drawio_inventory.py`, módulos exclusivos, secuencia, contratos, permisos derivados de conectores y guardrails; el esqueleto IaC solo se genera si se pide y se entrega por handoff (`terragrunt-iac` para Terraform/OpenTofu/Terragrunt); para el tipo de motor de datos de cada `16.xx` sigue `references/guia-catalogo-bases-de-datos.md`, y si el proyecto llama a un LLM, `17.4`/`17.5` siguen además `references/guia-costos-ia.md` para el rango de costo de tokens. Para `17.1`-`17.3`, sigue `references/drawio-iconos-nube.md`, resuelve iconos desde el catálogo curado, usa la referencia neutra solo como composición y ejecuta el validador estricto. Conserva IDs `CT-xx`, `API-xxx`, `API-xxx-OP-xxx`, `DATA-xxx` y `archiIconId` estables, actualiza `04`/`10.1` y registra decisiones para consolidarlas en `20`. Ejecuta `CP-03 Integridad del diseño` después de `17`, o después de `16` si despliegue no aplica; no avances con capacidades perdidas, operaciones priorizadas en `Propuesta`, persistencias narradas sin modelo, elementos críticos huérfanos o desviaciones sin decisión. Si el TO-BE define, cambia o retira bases de datos (motor en `09`/`10`/`10.1`, `16`, `16.xx`, `16.xx.y` o servicios de datos en `17`) y la skill `dba` está disponible, solicita su modo `design-review` antes de `CP-03` y dispone cada observación `DB-NNN` según `references/guia-catalogo-bases-de-datos.md` §8; si no está disponible, regístralo en `16` y continúa.
    Para una interfaz conversacional, el `14.xx` frontend mapea `SURF/SCR/CMP/ST/ERR/TC` de Iris
    a componentes, runtime y adaptadores; `14.00` y el contrato ejecutable poseen el protocolo y
    schemas; los `14.xx` backend/agente poseen relay, correlación, persistencia, idempotencia y
    confirmación. Si se selecciona AG-UI o A2UI, declara versión/baseline, transporte, mapping de
    eventos/surfaces, catálogo permitido, validación y fallback; el nombre de una librería UI no
    sustituye el contrato.
11. Genera `18-Tacticas-y-Patrones.md` siguiendo `references/guia-tacticas-patrones.md` y usando `references/guia-catalogo-tacticas-calidad.md` y `references/guia-catalogo-patrones.md`. Revisa explícitamente táctica arquitectónica, patrón arquitectónico, patrón de diseño, patrón cloud y patrón de IA; incluye los aplicados, su matriz `QA → TP → CT → DA → prueba`, fichas detalladas y Mermaid cuando explique una interacción, estado o fallo no evidente. Después genera `19-Dimensiones-Arquitectonicas.md`, incluyendo patrones de IA aplicables y la matriz transversal `CC-xxx` de `references/guia-clean-code.md`. Evalúa la aplicabilidad de `19.1` y, si corresponde, genera `19.1-Modelo-de-Amenazas-y-Requisitos-de-Seguridad_<Proyecto>.md` siguiendo `references/guia-modelo-amenazas-y-requisitos-seguridad.md`; conserva IDs estables `THR-xxx`/`SEC-xxx` y entrega a Vulcano criterios verificables, no herramientas ni diseño de pipeline. Si `aegis` reporta estados de `SEC-xxx` o `THR-propuesta-NN` observados en código, incorpóralos según la sección 10 de esa guía. Consolida por primera vez `20-Decisiones-Arquitectonicas.md`, y genera `21-Riesgos-y-Deuda-Tecnica.md` y `22-Glosario.md`. Completa en `02` el resumen de 3-5 objetivos de calidad. Desde este punto, `19.1` y `20` quedan vivos durante revisión y aprobación. Ejecuta `CP-04 Reconciliación` después de `22` o, en Caso C, después de `24`.
    Si hay agentic/generative UI, `18` documenta adapter/protocol/HITL como patrones solo cuando
    exista driver; `19.1` cubre payload/component/action injection, bypass de confirmación,
    exposición de PII/estado, autorización server-side y supply chain del renderer; `20` registra
    la configuración final por capas y candidatos descartados; `21` conserva lock-in, madurez,
    migración y deuda residual.
12. Ejecuta la auditoría interna y genera `25-Revision-Tecnica-Arquitectura.md` siguiendo `references/guia-auditoria-coherencia-arquitectura.md` y `references/guia-gobierno-validacion.md`: incluye snapshot/hash, matriz de compromisos, trazabilidad bidireccional, contradicciones/huérfanos, indicadores, ATAM y dictamen. Ejecuta `scripts/validate_architecture_coherence.py <directorio> --scenario A --strict`; cualquier error o bloqueante deja el dictamen `No apto` y el artefacto en `No cumple`.
13. Después de una ronda de `25`, genera `25.1.1-Manifiesto-Presentacion_<Proyecto>.json` y `25.1-Presentacion-Comite-Arquitectura_<Proyecto>.html` siguiendo `references/guia-presentacion-comite-arquitectura.md`. La presentación resume y enlaza la evidencia; nunca reemplaza los artefactos dueños. Solo puede quedar apta para aprobación si `25` no tiene bloqueantes; en caso contrario genera una versión `BORRADOR — NO APTO PARA APROBACIÓN`.
14. Presenta `25.1` al cliente o Comité de Arquitectura y genera `26-Validacion-y-Aprobacion.md`. Si se rechaza, vuelve al primer artefacto afectado, actualiza el manifiesto/presentación y repite `25`-`26`.
15. Solo después de aprobación, genera `00-Documento_Arquitectura_<Proyecto>.md` como orquestador corto.

Sigue `references/guia-gobierno-validacion.md` para los gates `07`, `10`-`13` y `25`-`26`; usa `references/guia-presentacion-comite-arquitectura.md` para producir `25.1`.

## Caso B: documentación AS-IS

Describe lo que el código hace, no lo que debería hacer.

1. Escanea dependencias, estructura, puntos de entrada, datos, integraciones, comunicación, contratos y rutas/controllers/endpoints/topics/schemas/clientes de API, patrones observables, fronteras de confianza, controles de aplicación observables, configuración de formato/lint/análisis/pruebas, CI/CD e IaC. En frontends inspecciona repositorios/builds, shell/host, remotes, routing, composición runtime/build/server-side, design system, estado compartido y despliegues independientes antes de afirmar Microfrontends. Si el repositorio es grande, primero mapea estructura y puntos de entrada.
2. Genera `02`-`06` según la evidencia real; omite `01` si no se necesita confirmar una línea base objetivo, y omite `07`-`13` porque no hay propuesta que seleccionar.
3. Para despliegue, reutiliza documentación vigente; si no existe, deriva `17` y `17.1`-`17.3` desde IaC siguiendo `references/guia-terraform-a-diagrama.md` (Terraform, Terragrunt, CloudFormation/SAM/CDK sintetizado, ARM/Bicep). Si la IaC revela cuentas múltiples, red compartida, conectividad híbrida, accesos entre cuentas o runners propios, documenta `17.6` en modo observado: cada confianza, ruta y segmento con evidencia; credenciales de larga duración, roles con comodines o imágenes `latest` son hallazgos en `21`. En ambos casos normaliza la representación con `references/drawio-iconos-nube.md` y valida catálogo, proveedor y `archiIconId`; no cambies la topología observada solo para ajustarla a la referencia. Si no hay evidencia, pregunta o registra la limitación en `04-Supuestos.md`.
4. Genera primero `10.1-Arquetipo-de-Solucion_<Proyecto>.md` en estado `Observado` siguiendo `references/guia-arquetipo-solucion.md`, con tecnologías/versiones/hosting sustentados por código, configuración o IaC y `Selección: No aplica — perfil AS-IS`. Después genera `14`-`22` y actualiza `10.1` con los `CT-xx` y enlaces definitivos. Clasifica todos los contenedores y genera `14.xx`/`16.xx` para los significativos. En datos AS-IS inspecciona también DDL, migraciones, ORM, esquemas, índices y políticas de retención: asigna `DATA-xxx`, separa modelo observado de inferencia y enlaza la evidencia física cuando exista; su ausencia es un hallazgo, no permiso para inventarla. Si existen interfaces programáticas, genera `14.00` desde especificaciones, rutas/controllers, gateways, schemas, topics, clientes y pruebas siguiendo `references/guia-gobierno-y-diseno-apis.md`; conserva diferencias entre contrato publicado y comportamiento observado como hallazgos. Clasifica patrones y evalúa Clean Code. Evalúa `19.1` siguiendo `references/guia-modelo-amenazas-y-requisitos-seguridad.md`; cuando aplique, cada `THR-xxx`, `SEC-xxx`, control observado y ausencia debe enlazar evidencia reproducible o quedar como hallazgo. Cada relación, tecnología, API/operación, contrato, `DATA-xxx`, patrón y `CC-xxx` debe tener evidencia. `21` incluye deuda, riesgos residuales y hallazgos verificables. Ejecuta `CP-03` después de `14`-`17` y `CP-04` después de `20`-`22`, distinguiendo siempre evidencia `Implementada` de intención o diseño.
5. Genera `25` con la auditoría completa de `references/guia-auditoria-coherencia-arquitectura.md` y ejecuta `scripts/validate_architecture_coherence.py <directorio> --scenario B --strict`; después genera y valida `25.1.1`/`25.1` como presentación de evidencia AS-IS, presenta para validación y genera `26`. Después de aprobación, genera `00-Arquitectura_AS-IS_<Proyecto>.md`.

## Caso C: AS-IS a TO-BE

1. Genera o confirma primero el AS-IS siguiendo el Caso B.
2. Ejecuta el flujo completo del Caso A para el TO-BE, anclado a la evidencia del AS-IS. En `10.1` registra por scope y tecnología la transición `AS-IS → TO-BE` y qué se conserva, migra o retira.
3. Después de `22`, genera `23-Analisis-de-Brechas.md` y `24-Roadmap-de-Migracion.md` siguiendo `references/guia-as-is-to-be.md`. Si la transición migra datos o cambia de motor, pide a `dba` (si está disponible) su modo `data-migration` y refleja en `24` fases, CDC, validación de equivalencia, corte y rollback, disponiendo sus observaciones en `16.00.1`.
4. Ejecuta `25` distinguiendo `AS-IS` y `TO-BE` en la matriz de compromisos y valida con `scripts/validate_architecture_coherence.py <directorio-TO-BE> --scenario C --strict`; genera y valida `25.1.1`/`25.1`, y después ejecuta `26`. Si se aprueba, genera `00-Arquitectura_TO-BE_<Proyecto>.md`. Conserva separado el AS-IS aprobado.

## Reapertura incremental por cambios

Una capacidad, dato, integración, operación, requisito de seguridad o decisión agregada/cambiada después de un checkpoint invalida el cierre de todos los artefactos dependientes; no puede quedar “fuera del alcance de esta ronda” mientras se conserve dentro de la arquitectura vigente.

1. Registra el cambio y determina el primer documento dueño afectado (`02`/`06` para alcance, `14.00` para contrato, `16` para dato, `19.1` para seguridad o `20` para decisión).
2. Reabre sus checklists y los de sus dependientes a `No cumple` hasta reconciliarlos. Una marca `[x]` previa no sobrevive a evidencia nueva incompatible o incompleta.
3. Para una `FAS-xxx` nueva o modificada revisa como mínimo `10.1`, `14`, `14.00`, contratos ejecutables `14.xx.y`, `14.xx`, `15`, `16`/`16.xx`/esquema físico aplicable, `17`, `18`, `19.1`, `20`, `21` y sus trazabilidades. Actualiza solo los que apliquen, pero registra explícitamente cada `N/A`. Si el cambio agrega o modifica campos de una integración `EXT-xx` con `14.xx.N` propio, actualízalo también y reconcilia sus incertidumbres/riesgos enlazados en `12`/`21`.
4. Repite `CP-03` y `CP-04`, recalcula el snapshot/hashes de `25`, reejecuta el validador completo y regenera `25.1`; si ya existía una decisión en `26`, crea una nueva ronda de validación humana.
5. No promociones una operación priorizada de `Propuesta` a cierre por narrativa: debe aparecer en el catálogo dueño y en un contrato procesable validado. Tampoco declares persistencia por narrativa: debe existir un `DATA-xxx` y una fila de cobertura en el `16.xx` dueño.

## Reglas de diagramas

- **Antes del primer diagrama de la sesión, lee `references/guia-calidad-visual-diagramas.md`.** Es la dueña de la notación, los conectores, el presupuesto de complejidad y la composición `.drawio`; sus reglas aplican a todo diagrama, generado a mano o con MCP. Declara el plan de diagramas (pregunta que responde cada uno, formato y divisiones por presupuesto) antes de dibujar.
- Todo Markdown con Mermaid pasa `scripts/validate_mermaid.py <archivo> --strict` (con el parser oficial para compilación real; si no está disponible, regístralo como no verificado). Todo `.drawio` pasa `scripts/validate_drawio_catalog.py` y `scripts/validate_drawio_layout.py` en modo `--strict`.
- En `09`, cada sección `### Alternativa <ID> — <Nombre>` contiene obligatoriamente un Mermaid propio que represente esa configuración bajo el mismo nivel de abstracción y la misma notación visual que las demás. Esta regla aplica aunque estén disponibles MCP de diagramación; Excalidraw, draw.io o un Mermaid comparativo pueden agregarse como apoyo, pero no reemplazan el bloque Mermaid de ninguna alternativa.
- Todo `.excalidraw` pasa `scripts/validate_excalidraw.py <archivo> --strict --owner <dueño>.md`; todo diagrama interactivo se genera con `scripts/build_interactive_diagram.py <spec> -o <html> --strict --owner <dueños>` y su página reporta `archValidate()` vacío. Los `.excalidraw` se nombran `<NN>.<k>-<Tema>_<Proyecto>.excalidraw` con el número del artefacto dueño y complementan, nunca reemplazan, su Mermaid o `.drawio`.
- Antes de cerrar cualquier diagrama, renderízalo y míralo (`scripts/render_preview.py` para `.drawio`/`.excalidraw`, export real o navegador para el interactivo) y corrige lo que veas: solapamientos, textos cortados, conectores sobre nodos, etiquetas que no caben.
- Embebe C4 y secuencias como Mermaid en Markdown, salvo despliegue AWS/Azure/GCP, que usa `.drawio` con iconografía oficial curada. Genera una sola página y un proveedor por archivo, XML sin compresión, `archiIconId` en cada recurso y ninguna biblioteca legada o mezclada.
- C4 niveles 1 y 2 son obligatorios a nivel de sistema. C4 Nivel 3 es obligatorio en un `14.xx` separado para cada contenedor significativo; nivel 4 solo cuando una parte crítica requiera detalle de código. Para Microfrontends, modela como `CT-xx` solo shell/remotes construibles, versionables y desplegables independientemente; un módulo compilado con el portal es componente de su `14.xx`.
- Genera secuencias solo para flujos críticos, incluyendo rutas de error relevantes.
- En `18`, genera Mermaid cuando lo exija `references/guia-tacticas-patrones.md`: usa secuencia para interacciones, estados para ciclos de vida y flowchart para decisiones/fallback. No dupliques un flujo ya dueño de `15` ni generes diagramas decorativos.
- Genera un modelo de datos `16.xx` por cada contenedor significativo con datos persistentes o estado no trivial; declara su madurez y la cobertura de cada `DATA-xxx`. Si el objetivo es listo para implementación, agrega además el esquema físico procesable `16.xx.y` y el diccionario exhaustivo definido en `references/guia-diccionario-fisico-datos.md`: cada tabla/colección/vista/proyección y cada campo debe quedar documentado y corresponder con el asset. Para contenedores sin modelo propio registra `No aplica` y la razón. Genera otros diagramas cuando aporten información no cubierta.
- Consulta `references/diagramas-c4-ejemplos.md`, `references/diagramas-adicionales-ejemplos.md` y `references/drawio-iconos-nube.md`; sus ejemplos ya cumplen la guía visual y pasan los validadores. Para Azure puedes usar `assets/drawio/referencia-despliegue-azure.drawio` solo como guía de jerarquía visual; reemplaza todos los `[CT-*]` y no copies su selección de servicios.

## Plantilla y reglas de contenido

Usa `references/plantilla-documento-arquitectura.md`. Cada tema tiene un único archivo dueño; los demás citan su ID y enlazan. `10.1` posee los arquetipos `ARQ-xxx`, la especificación de sus scaffolds implementables y el baseline tecnológico canónico; sigue `references/guia-arquetipo-solucion.md` y mantenlo vivo hasta `25`. `14` y `16` son índices maestros y sus `14.xx`/`16.xx` poseen el detalle por contenedor. `16` posee el catálogo canónico `DATA-xxx`; cada `16.xx` posee su modelo y matriz de cobertura, y cada `16.xx.y` físico pertenece al mismo contenedor. `14.00` posee el gobierno transversal y catálogo canónico `API-xxx`/`API-xxx-OP-xxx`; los contratos ejecutables pertenecen al `14.xx` del contenedor owner. Cada `14.xx.N` de mapeo de integración externa pertenece al mismo `14.xx` dueño del adaptador/ACL; no mantiene un registro de gaps propio, alimenta `12`/`21`. `18` consolida patrones; `19` posee Clean Code `CC-xxx`; `19.1` posee amenazas `THR-xxx`, requisitos arquitectónicos `SEC-xxx` y el handoff a Vulcano. Vulcano posee la operacionalización DevSecOps: herramientas, stages, escáneres, umbrales, SLA, SBOM, firma/provenance, policy as code y evidencia continua. `04`, `10.1`, `14.00`, `16`, `19.1` y `20` son vivos hasta `25`. Omite artefactos condicionales que no apliquen, pero nunca renumeres los restantes.

Aplica los "Criterios de cierre por artefacto" de la plantilla como contrato de calidad:

- Empieza cada Markdown generado, salvo `00`, con `## Tabla de Contenido` justo después del título (y el comentario `<!-- Document ID -->` y la línea de contexto inicial, si existen) y antes del primer encabezado de contenido, siguiendo `references/plantilla-documento-arquitectura.md`. Enlaza cada `##` y, cuando el documento catalogue entradas con ID estable en `###`/`####` (`TP-xxx`, `DA-xxx`, `QA-xx`, `ARQ-xxx`, `Alternativa <ID>`, Análisis ATAM por `QA-xx`, etc.), cada entrada; no enlaces las subsecciones de ficha que se repiten idénticas dentro de cada entrada (p. ej. "Mecanismo", "Trade-offs"). Actualízala si agregas, renombras o quitas encabezados antes de cerrar el artefacto. En `00` la tabla `## Índice` ya cumple esta función de navegación y no se duplica.
- Termina cada Markdown generado con `## Criterios de cierre`, estado, checklist aplicable y evidencia u observaciones. Copia los criterios del artefacto sin sustituirlos por frases genéricas.
- Marca `[x]` únicamente cuando exista evidencia observable dentro del documento o mediante enlace. Todo criterio aplicable pendiente conserva `[ ]` y deja el artefacto en `No cumple`; `Cumple con observaciones` exige todos los criterios cumplidos y solo admite mejoras adicionales no bloqueantes con responsable y fecha.
- No cierres un artefacto, sus dependientes ni el siguiente gate mientras esté en `No cumple`. Puedes elaborar documentos relacionados en paralelo, pero mantenlos en borrador y revalídalos al cerrar la dependencia. Como excepción, el borrador `05` puede avanzar a `07` para completar su priorización, pero debe quedar en `Cumple` antes de `08` o `09`.
- Para artefactos condicionales que no aplican, no generes archivos vacíos: registra `No aplica` y el motivo en su documento dueño o índice.
- Si solo una condición interna no aplica, marca ese ítem `[x] N/A — motivo` sin declarar todo el artefacto `No aplica`.
- Evalúa los criterios de `.drawio` y del HTML de costos `17.5` en `17-Vista-de-Despliegue.md`, bajo una subsección por archivo con fecha de revisión y SHA-256. Para cada `.drawio` registra además proveedor, `catalogVersion`, commit fuente del catálogo, comando/resultado del validador y excepciones. Evalúa `25.1` en una subsección posterior de `25`, con el hash del manifiesto y del HTML. Reevalúa `04`, `10.1`, `14.00`, `19.1` y `20` en `25` porque son documentos vivos.

## Antes de entregar

- Verifica trazabilidad entre `OBJ-xx`, `QA-xx`, `FAS-xxx`, alternativa, selección, `ARQ-xxx`/baseline tecnológico, decisiones, vistas, tácticas, `THR-xxx`/`SEC-xxx` y pruebas.
- En Casos A/C, verifica que `01` contenga `## Preparación del dominio`, que DR-01 esté `Listo` o `Listo con riesgos`, que la evidencia sea verificable, que `Handoff pendiente` y los hotspots arquitectónicos bloqueantes sean `Ninguno`, y que todo riesgo admitido se cierre antes de declarar `25` apto.
- Verifica los cuatro checkpoints de `references/guia-auditoria-coherencia-arquitectura.md` y que `25` audite en ambas direcciones: cada compromiso llega a una respuesta/evidencia y cada `ARQ/CT/API/TP` material tiene driver o decisión.
- Comprueba que QAW, selección, incertidumbres y PoC aplicables estén cerrados antes de `14`.
- Verifica que `09` use un mapa de alcance común, permita configuraciones mixtas y no trate Hexagonal/CQRS como alternativas macro; que cada encabezado `### Alternativa <ID> — <Nombre>` incluya dentro de su sección un bloque Mermaid propio, lógico y compilable; que `10` conserve la asignación aprobada de cada capacidad; y que `14` materialice esa asignación sin convertir automáticamente bounded contexts en microservicios.
- Verifica que `10.1` cubra cada scope con `ARQ-xxx`; que inventaríe y detalle cada arquetipo implementable con características, estructura de carpetas, patrones/controles, contrato de desarrollo, configuración, aceptación y relación con legado; que documente componentes compartidos, convenciones y prioridad; que cada tecnología tenga versión/baseline, uso, scope, estado, hosting, owner y evidencia/decisión; que `Pilotear` enlace `11`-`13`; y que el baseline coincida con `10`, `14`, `14.00`, `16`, `17` y `20`. Usa `05.04.06-Analysis-Archetypes.md` solo como ejemplo de profundidad, nunca como fuente tecnológica.
- Si hay interfaz conversacional/agentic UI, verifica que `10.1` no oculte la decisión bajo el
  framework frontend general: kit UI, runtime/estado, protocolo agente↔UI y UI generativa quedan
  identificados por separado o con `No aplica` justificado; toda configuración `Pilotear` tiene
  evidencia comparable en `11`-`13` y decisión consolidada en `20`.
- Comprueba que todos los contenedores estén clasificados, que cada significativo tenga `14.xx`, que cada significativo con estado relevante tenga `16.xx` y que las omisiones estén justificadas.
- Comprueba que `16` catalogue cada conjunto persistente relevante como `DATA-xxx`; que cada `16.xx` declare objetivo de entrega y madurez conceptual/lógica/física; que su matriz cubra `driver → API/OP/evento → esquema → DATA → entidad → estructura/store → operación → clasificación/retención`; y que todo dato que `14.xx`, `15`, `18`, `19.1` o un contrato describa como persistido tenga fila y modelo. Si el objetivo es listo para implementación, exige esquema físico procesable enlazado y validado más `## Diccionario físico de datos` según `references/guia-diccionario-fisico-datos.md`, con cobertura 1:1 de todos los objetos y campos físicos; si no lo es, exige condición, owner y momento para elevar la madurez.
- Verifica que cada `16.xx` declare el tipo de motor de datos elegido con justificación (`references/guia-catalogo-bases-de-datos.md`); si hubo 2+ motores real y actualmente viables sin trade-off obvio, que se haya aplicado `references/guia-matriz-decision.md` y quede un `DA-xxx` en `20` cuando la decisión no viva ya en `09`/`10`.
- Si existe `16.00.1-Observaciones-Datos_<Proyecto>.json`, verifica que ninguna observación `bloqueante` o `mayor` de `dba` quede `pendiente` o `diferida`, que `rechazada-justificada` y `riesgo-aceptado` tengan nota (y el riesgo esté en `21`) y que las `incorporada` se reflejen en el artefacto dueño; si el TO-BE define datos y no hay `16.00`, `16` debe declarar "Revisión experta de datos: No disponible" con motivo.
- Si `18`/`19` registran un patrón de IA con LLM, verifica que `17.4`/`17.5` incluyan el desglose de tokens de `references/guia-costos-ia.md` con rango entre modelos candidatos — "sin modelo elegido" nunca deja la partida como "No estimable".
- Si existen interfaces programáticas, comprueba que `14.00` siga `references/guia-gobierno-y-diseno-apis.md`: alcance y nomenclatura explícitos; `API-xxx`/`API-xxx-OP-xxx` estables; owner, consumidor, exposición, seguridad, estado, contrato y trazabilidad; contratos ejecutables válidos bajo su `14.xx`; compatibilidad y transición AS-IS/TO-BE cuando aplique.
- Si existe algún `14.xx.N` de mapeo de integración externa, verifica `references/guia-mapeo-integraciones-externas.md#6`: fuentes consultadas con tipo/fecha/ubicación; si hubo Postman, que el conteo del script coincida con lo documentado o la diferencia esté registrada; cada interacción enlaza un `API-xxx-OP-xxx`/`EXT-xx` real de `14.00`; mapeo campo a campo en ambas direcciones para lo consumido; ejemplos sin datos reales identificables; y ningún registro de gaps propio — los vacíos viven en `12`/`21`.
- Para streaming, WebSocket, SSE o eventos conversacionales, comprueba además esquemas discriminados de eventos, orden, correlación, idempotencia, reconexión/reanudación, cierre y errores; “streaming” sin protocolo y contrato de mensajes no alcanza estado `Definida`.
- Cuando el frontend implemente artefactos Iris, comprueba la trazabilidad
  `SURF/SCR/CMP/ST/ERR/TC → componente/runtime/protocolo/adaptador → API/OP/contrato → prueba`.
  Para UI generativa exige catálogo allowlisted, validación, acciones autorizadas y fallback; una
  capacidad del framework sin mapping verificable no cuenta como cobertura.
- Comprueba consistencia de IDs `CT-xx`, `API-xxx`, `API-xxx-OP-xxx`, contratos, ownership y nombres entre `14`, `14.00`, `14.xx`, `15`, `16`, `16.xx`, `17` y `20`, además de despliegue y costos `17.1`-`17.5`.
- Ejecuta `scripts/validate_mermaid.py resources/architecture/*.md --strict` y registra el resultado; un bloque que no compila o rompe las reglas de `references/guia-calidad-visual-diagramas.md` deja su artefacto en `No cumple`.
- Para cada `17.1`-`17.3`, ejecuta `scripts/validate_drawio_catalog.py --drawio <archivo> --provider <proveedor> --strict` y `scripts/validate_drawio_layout.py --drawio <archivo> --strict`; verifica una página, XML auditable, ausencia de `[CT-*]`, proveedor único, cero bibliotecas legadas, `archiIconId` trazable y coherencia topológica con `14`/`17`. No uses `--reference` para aprobar entregables.
- Si `17.6` aplica, verifica sus criterios de cierre de `references/guia-infraestructura-cloud.md` §11: cuentas con owner y guardrails, plan de direccionamiento sin solapamientos, matriz de comunicación entre segmentos, ambos lados de cada confianza entre cuentas, runners con red/identidad/aislamiento, cero banderas 🔴 abiertas y cargos de red en `17.4.1`.
- Si `17.7` aplica, verifica que `17.7.1` provenga de `scripts/extract_drawio_inventory.py` sobre los `.drawio` aprobados (con hash), que inventario = suma de módulos, que la secuencia sea acíclica, que cada permiso provenga de un conector y que el análisis descriptivo no contenga recomendaciones; un esqueleto IaC sin validación registrada no se entrega.
- Si `08` profundiza a nivel de pregunta, verifica que cada HRI tenga riesgo en `21` y que ninguna pregunta quede sin estado; `08.1` no contiene `QuestionId`/`ChoiceId` inventados.
- Verifica que supuestos, decisiones, riesgos y hallazgos tengan ID único y archivo dueño.
- Si `19.1` aplica, verifica alcance, trust boundaries, amenazas priorizadas, criterios `SEC-xxx`, riesgos residuales y trazabilidad a `CT/API/OP/DA/TP`; cada `SEC-xxx` debe tener handoff a Vulcano o motivo explícito de no automatización. No bloquees arquitectura greenfield por ausencia de pipeline, pero no presentes intención como implementación.
- Verifica que cada Markdown aplicable incluya su checklist de cierre y que `17` evalúe los `.drawio` y `17.5`; consolida en `25` el estado y la evidencia de los artefactos aplicables generados hasta `24` y sus assets. Después de generar `25.1`, agrega en `25` su validación local, hashes y estado. `25`, `26` y `00` se cierran con su checklist local al generarse.
- Verifica que `25.1` tenga las vistas `Ejecutiva`, `Arquitectura` y `Completa`, evidencie el trabajo realizado, enlace sus fuentes, use assets locales, exponga faltantes/contradicciones y no duplique ni invente la verdad canónica. Ejecuta `scripts/validate_architecture_presentation.py` antes de presentarla.
- Confirma que `25` no tenga bloqueantes abiertos, que `25.1` sea apta para aprobación y que `26` contenga aprobación humana explícita. El agente nunca se autoaprueba.
- Ejecuta `scripts/validate_architecture_coherence.py <directorio> --scenario <A|B|C> --strict` después de cerrar `25` y registra la salida. Si cambia una fuente, repite el checkpoint afectado, actualiza hashes/ATAM/dictamen, reejecuta la auditoría completa y regenera `25.1`.
- Verifica que todos los artefactos estén numerados y dentro de `resources/architecture/`.
- Verifica que cada Markdown generado, salvo `00`, tenga `## Tabla de Contenido` sincronizada con sus encabezados `##` y sus entradas catalogadas por ID; una tabla ausente o incompleta deja el artefacto en `No cumple`.
- Verifica que `02` asigne `OBJ-xx` a los objetivos de negocio e incluya interesados y contexto técnico; que cada `QA-xx` de `05` enlace al menos un `OBJ-xx`, complete todos sus campos y aparezca en la tabla resumen de priorización; que `10` cierre con la síntesis de estrategia; que `14` contenga la matriz de cobertura; que cada `14.xx` trace `QA-xx`/`FAS-xxx`; y que cada `DA-xxx` de `20` tenga `Estado`.
- Verifica que `07` clasifique los 13 atributos — incluida Seguridad — y `08` los 6 pilares Well-Architected, cada uno con estado explícito (`Priorizado`/`Cubierto`, `Considerado y descartado`, o `No aplica`) y motivo cuando corresponda — ninguno sin fila en su matriz de cobertura.
- Verifica que `18` cubra cada `QA-xx` priorizado o justifique la ausencia de táctica, que cada `TP-xxx` tenga ficha, estado, owner, parámetros, fallos, trade-offs, validación y enlaces `CT/DA`, y que los Mermaid justificados compilen sin duplicar `15`.
- Verifica que `18` clasifique los cinco tipos con estado/motivo y aplique la propiedad por faceta de `references/guia-catalogo-patrones.md`: `09` compara configuraciones macro y `10` registra selección; `14.xx` posee Hexagonal/Capas y patrones locales; `14.xx`/`16.xx` poseen CQRS localizado; `17` el despliegue/patrones cloud; `19` la evaluación transversal de patrones IA; `18` indexa y valida; `20` posee el razonamiento de decisión. No dupliques contenido ni patrones sin problema demostrado.
- Si Microfrontends fue seleccionado u observado, verifica `references/guia-microfrontends.md`: driver y alternativa simple, scope/owner, shell y unidades desplegables, clasificación `CT-xx` correcta, contratos/estado/UX/seguridad, compatibilidad, rendimiento, capacidad de entrega independiente, observabilidad y rollback; enlaza pipeline AS-IS/Vulcano cuando exista. Si fue descartado, registra el motivo en `09`/`18` sin generar contenedores ficticios.
- Verifica que `19` defina reglas `CC-xxx` con automatización, umbral, owner, estado, evidencia de definición y evidencia de ejecución; que cada `14.xx` con código las aplique o justifique; que Caso C separe AS-IS/TO-BE; y que `25` no declare una regla `Aplicada` o `Validada` sin evidencia reproducible.
- Verifica que `19.1` no duplique la estrategia DevSecOps de Vulcano: puede exigir una clase de evidencia, pero no seleccionar scanners, comandos, stages, severidades de bloqueo, SLA operativos, formato SBOM, firma/provenance ni motores de policy as code.
- Genera `00` al final y mantenlo entre 100 y 150 líneas: propósito, resumen, stakeholders, estado de aprobación e índice.

## Registro de avance en memoria

Al terminar tu tarea, deja un nodo de avance en la memoria del proyecto (skill
[`memoria`](../memoria/SKILL.md)) con el payload mínimo
`{ "skill": "archi", "type": "avance", "title": "...", "summary": "..." }`:

    node .claude/skills/memoria/scripts/memoria.mjs record \
      --skill archi --type avance --title "..." --summary "..." \
      --file <ruta del artefacto> [--link <id-del-nodo-previo>]

O escribe ese payload como JSON en `.memoria/pending/<timestamp>.json`: el hook de Stop
lo consolida en `.memoria/graph.json` al cerrar el turno. Si la misma tarea ya tiene nodo
(mismo `skill` + `title`), actualízalo en vez de duplicarlo.
