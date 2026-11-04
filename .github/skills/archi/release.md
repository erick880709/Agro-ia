# Release del skill `archi`

**Rama:** `docs/archi-artifacts`
**Base comparada:** `main` en `bf25fff`
**Corte documentado:** `910cbcd` más mejoras locales de Microfrontends, gobierno de APIs, handoff de seguridad Archi/Vulcano y gobierno visual draw.io pendientes de commit
**Fecha:** 2026-08-04
**Estado:** implementado y validado; la aprobación de arquitecturas generadas continúa siendo humana.

## Ajuste posterior — 2026-11-02: diagramación explicativa, Excalidraw e interactiva

Mejora el modo de diagramar a partir de `cathrynlavery/diagram-design`, `microsoft/devsquad-copilot` (`diagram-design`), `coleam00/excalidraw-diagram-skill`, `konraddzbik/architecture-diagram-skill` y `tt-a1i/archify`.

**Nuevo**

- `references/guia-diseno-diagramas.md`: método previo a dibujar (pregunta, audiencia, patrón semántico, tipo y herramienta, recortes), enrutador hacia el artefacto dueño, multi-zoom, evidencia concreta, deltas AS-IS→TO-BE, accesibilidad, bucle renderizar → mirar → corregir, importación con bitácora de fidelidad y exportación (draw.io CLI/Docker con `--embed-diagram`, Mermaid `:::mermaid` en Azure DevOps).
- `references/guia-excalidraw.md`, `scripts/validate_excalidraw.py` (con `--self-test` e `--inventory`) y `assets/ejemplo-argumento-outbox.excalidraw`: diagramas explicativos con paleta semántica de archi, flechas en codo, vinculaciones bidireccionales, construcción por secciones y cruce de IDs con el artefacto dueño.
- `references/guia-diagramas-interactivos.md`, `assets/plantilla-diagrama-interactivo.html`, `scripts/build_interactive_diagram.py` y `assets/ejemplo-flujos-interactivos.json`: artefacto condicional `15.1`/`15.1.1` con flujos paso a paso, modos AS-IS/TO-BE, panel de payload y `SEC-xxx`, fronteras de confianza, enrutamiento ortogonal que rodea nodos, enlaces profundos, tema claro/oscuro, accesibilidad y `archValidate()`.
- `scripts/render_preview.py`: vista previa PNG de `.drawio` y `.excalidraw` (Pillow) que reporta etiquetas superpuestas o sobre nodos.
- `tests/test_diagramas.py`.

**Actualizado**

- `SKILL.md`, `guia-calidad-visual-diagramas.md` (validadores, tabla de alcance y checklist con revisión visual), `guia-mcp-diagramacion.md` y `guia-presentacion-comite-arquitectura.md` (enlaces profundos al interactivo y exports).

## Ajuste posterior — 2026-10-30: infraestructura cloud y blueprint de IaC

Mejora la capa de infraestructura a partir de repositorios y materiales de referencia de AWS: `aws-samples/aws-cloud-wan-blueprints`, `aws-solutions-library-samples/guidance-for-developing-infrastructure-as-code-templates-from-architecture-diagrams-on-aws`, `aws-samples/architecture-to-cloudformation`, `aws-samples/sample-well-architected-acceleration-with-generative-ai` (tópico `aws-well-architected-tool`), `arquitecto-java/java-letters-api`, la skill comunitaria `sagochiko/aws-drawio-diagram-skill` (tópico `aws-architecture`) y los blogs de AWS sobre runners de GitHub Actions en CodeBuild y ECS.

**Nuevo**

- `references/guia-infraestructura-cloud.md` y artefacto condicional `17.6-Infraestructura-Base_<Proyecto>.md`: organización y cuentas, identidad de máquinas y acceso entre cuentas, topología de red (peering, Transit Gateway, Cloud WAN, PrivateLink, VPC Lattice y equivalentes Azure/GCP), reglas de diseño y restricciones de Cloud WAN, inspección/egress/híbrido/DNS, registro central, runners de CI/CD y intake por niveles con reporte de banderas 🔴/🟡/🟢.
- `references/guia-diagrama-a-iac.md` y artefactos `17.7-Blueprint-IaC_<Proyecto>.md` / `17.7.1-Inventario-Despliegue_<Proyecto>.json`: inventario determinista, análisis descriptivo sin recomendaciones, módulos exclusivos con conteos reconciliados, secuencia de despliegue, contratos, permisos derivados de conectores, guardrails, especificación de código y esqueleto opcional con ciclo validar-corregir; handoff a `terragrunt-iac`.
- `scripts/extract_drawio_inventory.py` (con `--self-test`): recursos con `archiIconId`, jerarquía de límites, conectores y hallazgos (íconos sin ID, conectores sin etiqueta, recursos aislados).
- Catálogo de íconos `1.2.0`: 40 íconos AWS de red, seguridad, gobierno, contenedores, datos, integración, IA y CI/CD verificados contra `Sidebar-AWS4.js` en el commit fijado (`3b42106`), con alias.

**Actualizado**

- `references/guia-well-architected.md`: revisión por pregunta (OPS 1-11, SEC 1-11, REL 1-13, PERF 1-5, COST 1-11, SUS 1-6) con HRI/MRI, mapa de evidencias por artefacto, lentes (Financial Services, Data Analytics y otras), separación análisis/recomendación y exportación opcional `08.1` sin identificadores inventados.
- `references/guia-terraform-a-diagrama.md`: mapeos de red, seguridad, gobierno y CI/CD; lectura de Terragrunt (units, stacks, jerarquía live) y CloudFormation/SAM/CDK.
- `references/drawio-iconos-nube.md`: composición AWS (servicios globales vs regionales, zonas con nombre real, flujo vertical, recursos implícitos vs opcionales).
- `SKILL.md` y `references/plantilla-documento-arquitectura.md`: numeración `08.1`, `17.6`, `17.7` con criterios de cierre y verificaciones previas a la entrega.

**Validaciones ejecutadas**: `validate_drawio_catalog.py --strict` (catálogo 97 íconos + referencia Azure), `validate_drawio_layout.py --strict` sobre la referencia, `extract_drawio_inventory.py --self-test` y sobre la referencia Azure, `validate_mermaid.py --strict` sobre las guías nuevas, `validate_architecture_coherence.py --self-test` y `tests/test_pricing.py`.

**Limitaciones**: los blogs de AWS y builder.aws.com no pudieron descargarse en el entorno de trabajo; la sección de runners se basa en documentación conocida y se marca para verificación. No se agregó todavía una referencia `.drawio` AWS equivalente a la de Azure.

## Ajuste posterior — 2026-10-13: diagramación profesional

Revisión de la capa de diagramas contra el código fuente de draw.io (commit fijado en el catálogo) y contra el repositorio de referencia `cathrynlavery/diagram-design`.

**Correcciones**

- Catálogo de íconos `1.1.0`: los 18 íconos AWS usaban `strokeColor=none`; en `resourceIcon` el glifo se pinta con `strokeColor`, por lo que se renderizaban como cuadrados vacíos. Ahora usan `strokeColor=#ffffff`, como la paleta oficial. Los estilos GCP3 se alinean con la paleta oficial (sin `fillColor` forzado).
- Catálogo: se agregan 7 límites AWS (`aws.group-*`: cloud, cuenta, región, VPC, subred pública/privada, datacenter corporativo). Antes la guía exigía dibujar límites, pero el validador estricto rechazaba los grupos oficiales AWS4 por no estar en el catálogo.
- Referencia Azure: conectores con `curved=0`, anclajes repartidos, el conector app → caché ya no atraviesa la base de datos y se agrega la leyenda que la guía exigía.
- Ejemplos Mermaid: C4 con `UpdateLayoutConfig`, IDs `CT/EXT/DATA`, tecnología en cada `Rel` y outbox en lugar de *dual write*; secuencia con `autonumber`, 7 participantes y ruta de error `alt`; despliegue fallback realmente on-premise; todos los `flowchart` con `curve: step` y conectores etiquetados.
- Guía MCP: pide autorización antes de modificar la configuración MCP del usuario.

**Nuevo**

- `references/guia-calidad-visual-diagramas.md`: dueña de las reglas visuales (notación estándar, conectores, presupuesto de complejidad, reglas por tipo y composición `.drawio`). La versión anterior de esta guía había quedado fuera del skill.
- `scripts/validate_mermaid.py`: reglas visuales y compilación real con el parser oficial de Mermaid (`mermaid@11.4.1` + `jsdom`), con autoprueba.
- `scripts/validate_drawio_layout.py`: composición del `.drawio` (conectores, cruces por nodos ajenos, solapamientos, desbordes, tamaños, grilla, anclajes, leyenda, presupuesto, glifo AWS), con autoprueba.

**Validaciones ejecutadas**: `validate_drawio_catalog.py --strict` (57 íconos), referencia Azure con catálogo y layout en estricto, `validate_mermaid.py --strict` sobre las 11 referencias con compilación real, autopruebas de ambos validadores nuevos y `validate_architecture_coherence.py --self-test`.

## Ajuste posterior — 2026-09-10

Se incorporó el gate `DR-01` de preparación del dominio para Casos A/C. Antes de generar arquitectura objetivo, `archi` clasifica la complejidad del dominio y exige Event Storming cuando existan procesos transversales, múltiples actores/estados, reglas, excepciones, compensaciones, integraciones o límites inciertos. Los dominios simples pueden usar evidencia equivalente validada y los alcances puramente técnicos pueden declarar `No aplica` con justificación.

El contrato se documenta en `references/guia-preparacion-dominio.md`, se registra en `01-Linea-Base_<Proyecto>.md` y se valida mediante `scripts/validate_architecture_coherence.py`. Los faltantes de propósito, alcance, métricas o decisiones de stakeholders regresan al orquestador para `epicureo`; los faltantes de comportamiento y límites de dominio regresan para `storming`. Caso B permanece exento mientras sea observación AS-IS.

## Contenido

0. [Ajuste posterior — 2026-10-30: infraestructura cloud y blueprint de IaC](#ajuste-posterior--2026-10-30-infraestructura-cloud-y-blueprint-de-iac)
0. [Ajuste posterior — 2026-10-13: diagramación profesional](#ajuste-posterior--2026-10-13-diagramación-profesional)
0. [Ajuste posterior — 2026-09-10](#ajuste-posterior--2026-09-10)
1. [Resumen](#resumen)
2. [Alcance de la release](#alcance-de-la-release)
3. [Cambios de arquitectura de la semana anterior](#cambios-de-arquitectura-de-la-semana-anterior)
4. [Proceso arquitectónico resultante](#proceso-arquitectónico-resultante)
5. [Características incorporadas](#características-incorporadas)
6. [Artefactos nuevos](#artefactos-nuevos)
7. [Artefactos y guías actualizados](#artefactos-y-guías-actualizados)
8. [Comportamiento por escenario](#comportamiento-por-escenario)
9. [Reglas de calidad y trazabilidad](#reglas-de-calidad-y-trazabilidad)
10. [Cambios de compatibilidad y migración](#cambios-de-compatibilidad-y-migración)
11. [Validaciones realizadas](#validaciones-realizadas)
12. [Historial de commits](#historial-de-commits)
13. [Limitaciones y condiciones](#limitaciones-y-condiciones)

## Resumen

Esta rama transforma `archi` de una guía general de documentación en un proceso arquitectónico gobernado, trazable y repetible. El skill ahora cubre el ciclo completo desde la línea base y los drivers hasta la selección, experimentación, diseño detallado, revisión técnica, presentación al comité y aprobación humana.

Las principales capacidades incorporadas son:

- numeración canónica alineada con el orden real de generación;
- gates explícitos para QAW, selección, tecnologías emergentes, incertidumbres, PoC, revisión y aprobación;
- criterios de cierre verificables para cada artefacto;
- checkpoints progresivos y auditoría formal de coherencia `prometido → diseñado → evidencia`, con trazabilidad bidireccional;
- diseño detallado y modelo de datos por contenedor significativo;
- alternativas consolidadas, distribuidas e híbridas definidas por alcance;
- un diagrama lógico Mermaid obligatorio dentro de cada alternativa, con validación automática de cobertura por sección;
- análisis de arquetipos implementables inspirado estructuralmente en `05.04.06-Analysis-Archetypes.md`, con scaffolds, árboles de carpetas, convenciones, legado y prioridad sin heredar sus decisiones tecnológicas;
- arquetipo de solución y baseline tecnológico vivo por proyecto;
- evaluación ATAM por escenario de calidad;
- catálogo y trazabilidad de tácticas y patrones;
- evaluación de Clean Code por contenedor;
- modelo de amenazas y requisitos de seguridad arquitectónica `THR-xxx`/`SEC-xxx` con handoff verificable a Vulcano;
- soporte cloud, multi-cloud, IaC, despliegue y costos;
- catálogo curado y versionado de iconos Azure/AWS/GCP, referencia visual neutra y validación determinista de `.drawio`;
- presentación HTML para sponsor, comité y revisores técnicos, derivada de evidencia y validada automáticamente.

## Alcance de la release

La comparación `main@bf25fff..910cbcd` contiene 12 commits exclusivos de la rama: 4 commits de artefactos de arquitectura realizados entre el 29 y el 31 de julio de 2026, y 8 commits de evolución del skill realizados el 3 de agosto de 2026.

El alcance específico del skill comprende:

- 28 archivos del skill creados o actualizados;
- aproximadamente 2.749 líneas agregadas y 190 eliminadas antes de incorporar este `release.md`;
- 17 archivos funcionales nuevos: 3 assets, 12 referencias/esquemas y 2 scripts;
- 2 scripts Python para generar y validar presentaciones;
- 3 assets reutilizables: plantilla DOCX, manifiesto JSON y plantilla HTML.

Después del corte `910cbcd`, el 4 de agosto de 2026 se incorporó la evaluación y diseño gobernado de Microfrontends mediante una referencia nueva y ajustes transversales en línea base, alternativas, arquetipo, C4, patrones, revisión y criterios de cierre. Esta mejora permanece pendiente de commit al momento de este documento.

En la misma fecha se incorporó el gobierno visual de despliegues cloud. Se tomó `resources/architecture/11.2-Despliegue_Azure_OCTO-HR.drawio` únicamente como antecedente de composición y se creó `assets/drawio/referencia-despliegue-azure.drawio`, neutra, de una página y sin topología de OCTO-HR. El catálogo masivo `resources/architecture/catalogo_iconos.json` se utilizó como insumo de descubrimiento, pero no se copió al contrato operativo: el nuevo `assets/iconos/catalogo_iconos_curado.json` contiene solo 50 iconos revisados, alias estables, estado, fallback, estilos y procedencia fijada.

El catálogo fija draw.io `31.1.5` y el commit `3b4210678207f3880888969ee53c9fe4580104ab`, con fuentes AWS4, Azure2 y GCP3. Se agregaron el esquema `catalogo_iconos.schema.json`, `aliases_iconos.json` y `scripts/validate_drawio_catalog.py`. El validador rechaza XML comprimido, múltiples páginas, placeholders, bibliotecas legadas, mezcla de proveedor, imágenes sin excepción y divergencias entre `archiIconId` y el estilo. La arquitectura continúa derivándose de C4, `10.1`, `17`, decisiones e IaC; catálogo y referencia no seleccionan servicios.

También se fortaleció `25` como auditoría independiente de coherencia. Los checkpoints `CP-01` a `CP-04` revisan drivers, selección/viabilidad, integridad del diseño y reconciliación antes del gate final. `25` incorpora snapshot con hashes, matriz de compromisos, trazabilidad inversa de elementos materiales, estados homogéneos de evidencia, contradicciones `CON-xxx`, indicadores, ATAM y dictamen. `scripts/validate_architecture_coherence.py` automatiza enlaces, IDs/owners, cierres, placeholders, cobertura, hashes, estados y bloqueantes sin sustituir la evaluación experta de suficiencia y trade-offs.

La release no cambia la ubicación de salida de los documentos generados: continúan en `resources/architecture/` o `resources/architecture/<Proyecto>/` para repositorios con varias iniciativas.

## Cambios de arquitectura de la semana anterior

La revisión de todas las referencias remotas de Azure DevOps encontró cuatro commits directos de arquitectura durante la semana calendario del 27 de julio al 2 de agosto de 2026. Los cuatro pertenecen a `origin/docs/archi-artifacts`, fueron realizados por `steve cardenas` y modifican artefactos generados o mantenidos por el proceso `archi`; no modifican directamente `.claude/skills/archi`.

| Commit | Fecha y hora (`UTC-05:00`) | Alcance | Resultado principal |
|---|---|---|---|
| [`94a5aba`](https://personalsoftsas.visualstudio.com/OCTO_IA_KIT/_git/OCTO_HR/commit/94a5aba75e15993f739e3e400faab05bd5a4c5f9) | 2026-07-29 16:55:29 | 7 archivos; 1.828 inserciones | Agregó documento de arquitectura, pricing, costos, línea base y diagramas AWS/Azure/GCP inicialmente generados por `archi`. |
| [`0ecb452`](https://personalsoftsas.visualstudio.com/OCTO_IA_KIT/_git/OCTO_HR/commit/0ecb45243b7b212f02780e383ca7c41b98cacee1) | 2026-07-30 16:20:24 | 29 archivos; 1.647 inserciones y 1.777 eliminaciones | Regeneró OCTO_HR con estructura numerada `00`-`16`, renombró artefactos y actualizó línea base/restricciones. |
| [`d43fe3a`](https://personalsoftsas.visualstudio.com/OCTO_IA_KIT/_git/OCTO_HR/commit/d43fe3a97fa4283a0a922def4f78c6471587cf42) | 2026-07-30 19:16:21 | 25 archivos; 8.051 inserciones y 497 eliminaciones | Actualizó alternativas, despliegue, pricing y costos; agregó `Presentacion Arq.html`, SVG y archivó artefactos anteriores. |
| [`270a216`](https://personalsoftsas.visualstudio.com/OCTO_IA_KIT/_git/OCTO_HR/commit/270a216e692461281000b1af2da9da7a0350e660) | 2026-07-31 15:04:45 | 9 archivos; 2.170 inserciones y 302 eliminaciones | Actualizó presentación y despliegue Azure; agregó DOCX, diagramas para Word, generador documental y RFP. |

También se identificaron tres commits compartidos con `main` que actuaron como insumos upstream. Se registran como antecedentes, pero no se cuentan entre los 12 commits exclusivos de la rama:

| Commit | Fecha y hora (`UTC-05:00`) | Relación con arquitectura |
|---|---|---|
| `ad760a0` | 2026-07-27 17:28:39 | Agregó contexto funcional y Event Storming de Atracción y Selección usado como fuente de drivers y bounded contexts. |
| `a005329` | 2026-07-28 11:34:28 | Incorporó hallazgos de inducción y actualizó eventos, actores, sistemas, comandos, políticas, entidades y hotspots. |
| `bf25fff` | 2026-07-28 15:32:11 | Agregó modelo de datos, proceso, presentación y libro de trabajo del Hub de Atracción y Selección; corresponde además a la base comparada. |

## Proceso arquitectónico resultante

La numeración expresa el orden del proceso. Los artefactos condicionales se omiten sin renumerar y `00` se genera al final para ordenar primero como orquestador.

| Orden | Artefacto o grupo | Propósito principal |
|---:|---|---|
| 01 | Línea base | Confirmar fuentes, contexto, stack, gobierno y autoridades |
| 02-04 | Contexto, restricciones y supuestos | Delimitar alcance, restricciones y vacíos vivos |
| 05-07 | Atributos, FAS y QAW | Identificar, estructurar y priorizar drivers |
| 08 | Well-Architected | Revisar holísticamente los seis pilares |
| 09 | Alternativas | Comparar configuraciones con un mapa común de alcance |
| 10 | Selección | Registrar decisión humana y asignación aprobada por scope |
| 10.1 | Arquetipo de solución | Consolidar arquetipos y baseline tecnológico vivo |
| 11-13 | Tecnologías, incertidumbres y PoC | Reducir riesgo antes del diseño detallado |
| 14/14.00/14.xx | Vistas C4, gobierno de APIs y diseño detallado | Diseñar el sistema, catalogar sus interfaces y detallar cada contenedor significativo |
| 15 | Secuencias | Explicar flujos críticos y rutas de error |
| 16/16.xx | Modelo de datos | Definir ownership global y detalle por contenedor |
| 17/17.1-17.5 | Despliegue y costos | Materializar topología cloud, diagramas y estimaciones |
| 18 | Tácticas y patrones | Trazar calidad, mecanismos, decisiones y pruebas |
| 19 | Dimensiones arquitectónicas | Consolidar aspectos transversales y Clean Code |
| 19.1 | Amenazas y requisitos de seguridad | Definir `THR-xxx`/`SEC-xxx`, riesgo residual y handoff a Vulcano cuando aplique |
| 20-22 | Decisiones, riesgos y glosario | Consolidar razonamiento, deuda y lenguaje común |
| 23-24 | Brechas y roadmap | Gobernar la evolución AS-IS a TO-BE |
| 25 | Revisión técnica | Auditar artefactos y ejecutar ATAM |
| 25.1 | Presentación de arquitectura | Exponer decisión y evidencia para distintas audiencias |
| 26 | Validación y aprobación | Registrar exclusivamente la decisión humana |
| 00 | Documento orquestador | Resumir y enlazar la versión aprobada |

## Características incorporadas

### 1. Gobierno y gates de arquitectura

- Se agregó una guía de gobierno para separar análisis, selección, experimentación, diseño y aprobación.
- El QAW exige participantes, mecanismo de priorización, votos o ranking, trade-offs, compromisos y lecciones aprendidas.
- La selección requiere autoridad, fecha, estado y confirmación humana; una recomendación no se considera seleccionada.
- Las tecnologías emergentes terminan en `Adoptar`, `Pilotear` o `Descartar`.
- Cada incertidumbre registra hipótesis, impacto, confianza, método, umbral, responsable y estado.
- Una incertidumbre crítica activa una PoC y bloquea el diseño hasta aprobarla o aceptar explícitamente el riesgo.
- La revisión `25` audita evidencia, consistencia, trazabilidad, contenedores, baseline, patrones, Clean Code y ATAM.
- El agente puede recomendar, pero no autoaprobar `10` ni `26`.

### 2. Criterios de cierre por artefacto

- Cada Markdown generado termina con `## Criterios de cierre`.
- Los criterios se expresan como checklist verificable y no como declaraciones genéricas.
- Estados permitidos: `Cumple`, `Cumple con observaciones`, `No cumple` y `No aplica`.
- Un criterio aplicable pendiente deja el artefacto en `No cumple`.
- `Cumple con observaciones` exige todos los criterios cumplidos y solo admite mejoras no bloqueantes con responsable y fecha.
- Los documentos vivos `04`, `10.1` y `20` se reevalúan en `25`.
- Los assets se controlan mediante versión o SHA-256 en su documento dueño.

### 3. Atributos de calidad y QAW

- `05-Atributos-de-Calidad.md` incorpora tabla resumen de priorización.
- Cada `QA-xx` contiene descripción, objetivo `OBJ-xx`, atributos relevantes, componentes SEI medibles, preguntas, problemas, prioridad y método de validación.
- Preguntas y problemas deben tener disposición explícita para evitar vacíos silenciosos.
- `07` recorre obligatoriamente 13 atributos de calidad, incluida Seguridad.
- Cada atributo queda `Priorizado`, `Considerado y descartado` o `No aplica` con motivo.
- La priorización de `05` debe coincidir con votos, ranking y orden registrados en `07`.

### 4. Well-Architected y ATAM

- Se agregó evaluación holística de los seis pilares Well-Architected.
- Los pilares no dependen únicamente de los atributos priorizados en QAW.
- Cada pilar queda cubierto, descartado justificadamente o no aplicable.
- `25` ejecuta ATAM sobre la arquitectura ya diseñada para cada `QA-xx` priorizado.
- El análisis registra enfoque, decisiones, sensibilidad, trade-off, riesgo y razonamiento.
- Se diferencia explícitamente la revisión de completitud de la evaluación de comportamiento arquitectónico.

### 5. Alternativas de solución híbridas por alcance

- Todas las alternativas parten del mismo mapa de capacidades o bounded contexts.
- Se pueden comparar configuraciones consolidadas, híbridas, distribuidas o definidas por el proyecto.
- Una alternativa híbrida puede combinar monolito modular, microservicios, workers, funciones y servicios administrados.
- Cada capacidad incluida se asigna a una unidad concreta y conserva sus drivers de separación o agrupación.
- El aislamiento se analiza en dimensiones lógica, datos, recursos, fallos y despliegue.
- Los bounded contexts no se convierten automáticamente en microservicios.
- Hexagonal y CQRS dejaron de tratarse como alternativas macro: se evalúan dentro del contenedor o scope donde resuelven un problema demostrado.
- La matriz de decisión incluye criterios, pesos, escala normalizada, evidencia y sensibilidad.
- Se incorporó evaluación de compra, reutilización, construcción o servicio administrado.

### 6. Arquetipo de solución por proyecto

- Se agregó `10.1-Arquetipo-de-Solucion_<Proyecto>.md` como perfil técnico canónico y vivo.
- Clasifica arquetipo principal y subarquetipos por scope mediante IDs `ARQ-xxx`.
- Consolida tecnologías, productos, versiones o políticas de baseline, uso, scope, hosting, owner, estado y evidencia/decisión.
- Permite estados de adopción como aprobado, piloto, retirada o excepción controlada.
- En Caso B registra el arquetipo observado; en Caso C separa `AS-IS → TO-BE`.
- Mantiene correspondencia con selección, contenedores, datos, despliegue, patrones, decisiones y riesgos.
- Un piloto se traza hacia `11`, `12` y `13`; una tecnología descartada obliga a revisar alternativa y selección.

### 7. Diseño detallado por contenedor significativo

- `14-Vistas-C4.md` conserva C4 Niveles 1 y 2 y clasifica todos los contenedores con IDs estables `CT-xx`.
- Cada contenedor significativo genera `14.xx-Diseno-Detallado_CT-xx_<Contenedor>.md`.
- Cada `14.xx` incluye C4 Nivel 3, responsabilidades, componentes, contratos, seguridad, resiliencia, observabilidad, riesgos y trazabilidad a drivers.
- Frontends, microservicios, workers, funciones y otros contenedores pueden ser significativos; la significancia no depende del tipo de tecnología.
- C4 Nivel 4 se reserva para partes críticas que realmente necesiten detalle de código.
- La numeración del contenedor permanece estable aunque se agreguen nuevos contenedores.
- `25` verifica que la asignación seleccionada en `10` se materialice sin pérdidas ni separaciones injustificadas.

El bloque `14` incorpora además `14.00-Gobierno-y-Catalogo-Inicial-de-APIs_<Proyecto>.md` cuando existen interfaces programáticas. Este documento posee la nomenclatura y buenas prácticas adoptadas, seguridad, compatibilidad, ciclo de vida y el catálogo estable `API-xxx`/`API-xxx-OP-xxx`. Cada `14.xx` aplica esas reglas y posee sus contratos ejecutables propios OpenAPI, AsyncAPI, Protobuf o GraphQL; los contratos externos enlazan la fuente autoritativa o un snapshot no canónico. `15` referencia las operaciones sin redefinirlas. Una API se delimita por capacidad, consumidores, ownership, seguridad y ciclo de vida, no automáticamente por microservicio o frontend.

### 8. Modelo de datos por contenedor

- `16-Modelo-de-Datos.md` actúa como mapa global de ownership y flujo de datos.
- Cada contenedor significativo con persistencia o estado no trivial genera su `16.xx` correspondiente.
- El mismo sufijo vincula `14.xx`, `16.xx` y `CT-xx`.
- El detalle cubre fuente de verdad, modelo conceptual/lógico/físico, agregados, transacciones, concurrencia, consistencia, seguridad, retención, migración y recuperación.
- Para CQRS localizado se documentan comandos, escritura, proyecciones, lag, reconstrucción y operación.
- Los contenedores sin modelo propio registran `No aplica` y motivo en el índice maestro.

### 9. Tácticas, patrones y Mermaid explicativo

- Se incorporó un catálogo maestro `TP-xxx` con trazabilidad `QA → TP → CT → DA → prueba/evidencia`.
- El skill distingue y revisa cinco categorías:
  - táctica arquitectónica;
  - patrón arquitectónico;
  - patrón de diseño;
  - patrón cloud;
  - patrón de IA.
- Se incluyen ejemplos y criterios para Circuit Breaker, Cache-Aside, Retry, Microservices, Event-Driven, Hexagonal, CQRS, Repository, Factory, Strategy, Observer, Sidecar, Ambassador, Strangler Fig, BFF, RAG, Context Engineering, Fine-tuning y Agent Pattern.
- Cada ficha documenta problema, mecanismo, alcance, parámetros, fallos, trade-offs, operación, validación, estado, owner y evidencia.
- Los patrones se incluyen solo cuando resuelven un problema demostrado.
- Se genera Mermaid cuando una interacción, estado, fallo, decisión o fallback no es evidente en texto.
- Los diagramas deben compilar, aportar explicación y no duplicar secuencias cuyo dueño sea `15`.

### 10. Clean Code como dimensión arquitectónica

- `19-Dimensiones-Arquitectonicas.md` incorpora un catálogo transversal `CC-xxx`.
- Cada regla registra alcance, automatización, umbral o condición de aceptación, owner, estado, excepción y evidencia.
- Cada `14.xx` con código propio aplica las reglas o justifica `No aplica`.
- Se separa evidencia de definición de evidencia de ejecución.
- En greenfield se permite estado `Definida`, pero no `Aplicada` o `Validada` sin evidencia reproducible.
- En AS-IS la evaluación se sustenta en código, configuración, análisis, pruebas o pipeline.
- En TO-BE se diferencian explícitamente estados AS-IS y TO-BE.

### 11. Cloud, multi-cloud, Terraform y costos

- Se reforzó la correspondencia entre contenedores lógicos y despliegue físico.
- Los diagramas AWS, Azure y GCP conservan numeración fija e iconografía oficial.
- Se documentan proveedor, región, ambientes, topología, red, identidad, escalado, alta disponibilidad, recuperación y puntos de fallo.
- Los patrones cloud se evalúan por alcance, seguridad, operación, costo, lock-in y modos de fallo.
- Terraform se usa como evidencia para derivar despliegues AS-IS cuando no existe documentación vigente.
- Las estimaciones exigen fecha, región, moneda, fuentes, dimensionamiento y totales verificables.
- El HTML de costos debe coincidir con el pricing y los diagramas de despliegue.

### 12. Presentación autónoma para comité

- Se agregó `25.1-Presentacion-Comite-Arquitectura_<Proyecto>.html` después de `25` y antes de `26`.
- El mismo HTML ofrece vistas `Ejecutiva`, `Arquitectura` y `Completa`.
- La presentación cubre decisión solicitada, valor, costo/plazo, trabajo realizado, gates, drivers, alternativas, selección, arquetipo, PoC, diseño, datos, cloud, tácticas, seguridad arquitectónica, decisiones, ATAM, riesgos y roadmap.
- El contenido proviene de un manifiesto JSON validable y no constituye una nueva fuente de verdad.
- Cada fuente recibe SHA-256 y enlace relativo; los assets de diagramas se mantienen locales para funcionamiento sin conexión.
- Los faltantes se muestran como `Missing evidence` y las contradicciones se registran explícitamente.
- Se contrastan proveedor, región, identidad, estilo, scope, tecnologías, versiones, contenedores, ownership, costos y decisiones.
- La presentación no puede declararse apta mientras existan bloqueantes, conflictos materiales o una selección no confirmada.
- Las versiones no aptas muestran permanentemente `BORRADOR — NO APTO PARA APROBACIÓN`.
- Se incluyeron generador y validador Python con modo estricto para sesiones de aprobación.

### 13. Evaluación y diseño de Microfrontends

- Se incorporó Microfrontends como patrón arquitectónico candidato, no como recomendación automática.
- `09` compara SPA modular, aplicaciones por ruta, composición runtime/server-side y alternativas híbridas cuando equipos, releases o migración lo justifican.
- Se prohíbe derivar un microfrontend por pantalla, bounded context o microservicio.
- `10` conserva la selección y scope humanos; `10.1` registra subarquetipo, shell, mecanismo, baseline, owners, capacidad de entrega y hosting, enlazando el pipeline AS-IS/Vulcano cuando exista.
- En C4 solo una unidad construible, versionable y desplegable independientemente recibe `CT-xx`; módulos publicados junto con el portal permanecen como componentes de `14.xx`.
- El diseño cubre shell/remotes, rutas, contratos, estado, design system, accesibilidad, identidad, dependencias, rendimiento, fallos, telemetría, pruebas y rollback.
- `17` gobierna CDN/edge, caché, compatibilidad, CSP/integridad, observabilidad, capacidad de entrega y despliegue independiente; Vulcano posee el detalle del pipeline y supply chain.
- `18` y `20` registran patrón, validación y trade-offs; `25` aplica un gate condicional para detectar falsa autonomía o acoplamiento oculto.
- Se agregó `references/guia-microfrontends.md` como fuente especializada y criterio transversal de cierre.

### 14. Seguridad arquitectónica y contrato con Vulcano

- Se agregó el artefacto condicional `19.1-Modelo-de-Amenazas-y-Requisitos-de-Seguridad_<Proyecto>.md`.
- `19.1` registra activos, datos, superficies, fronteras de confianza, amenazas `THR-xxx`, escenarios de abuso, requisitos verificables `SEC-xxx`, riesgo residual y excepciones.
- Cada `SEC-xxx` se traza a `CT/API/OP/DA/TP`, clase de evidencia, owner y criterio de aceptación.
- El handoff a Vulcano conserva los IDs y traduce requisitos a controles DevSecOps; no crea una segunda taxonomía.
- Archi no define scanners, stages, severidades de bloqueo, SLA operativos, SBOM, firma/provenance ni policy as code; esos elementos permanecen bajo Vulcano.
- La arquitectura greenfield puede cerrar requisitos en estado `Definido` cuando el handoff esté completo, sin afirmar un pipeline inexistente.
- Vulcano ahora descubre los nombres numerados vigentes de Archi y mantiene compatibilidad con rutas legacy.
- El validador de Vulcano contrasta los `SEC-xxx` de `19.1` contra la matriz de operacionalización de `08-security.md`; las omisiones son bloqueantes en cierre estricto.

## Artefactos nuevos

### Assets

- `assets/PS-ARQ-001 template.docx`: plantilla documental de arquitectura.
- `assets/plantilla-manifiesto-presentacion.json`: base estructurada para construir `25.1.1`.
- `assets/plantilla-presentacion-arquitectura.html`: presentación autocontenida y adaptable por audiencia.
- `assets/iconos/catalogo_iconos_curado.json`: catálogo canónico de 50 iconos Azure2/AWS4/GCP3 con procedencia fijada, estado y fallback.
- `assets/iconos/aliases_iconos.json`: resolución estable de términos tecnológicos a `archiIconId`.
- `assets/iconos/catalogo_iconos.schema.json`: contrato de estructura y compatibilidad del catálogo.
- `assets/drawio/referencia-despliegue-azure.drawio`: composición Azure neutra, auditable y sin topología de OCTO-HR.

### Referencias

- `references/guia-alternativas-solucion.md`
- `references/guia-auditoria-coherencia-arquitectura.md`
- `references/guia-arquetipo-solucion.md`
- `references/guia-catalogo-patrones.md`
- `references/guia-catalogo-tacticas-calidad.md`
- `references/guia-clean-code.md`
- `references/guia-diseno-detallado-contenedores.md`
- `references/guia-gobierno-validacion.md`
- `references/guia-gobierno-y-diseno-apis.md`
- `references/guia-matriz-decision.md`
- `references/guia-microfrontends.md`
- `references/guia-modelo-amenazas-y-requisitos-seguridad.md`
- `references/guia-presentacion-comite-arquitectura.md`
- `references/guia-tacticas-patrones.md`
- `references/guia-well-architected.md`
- `references/esquema-presentacion-arquitectura.json`

### Scripts

- `scripts/generate_architecture_presentation.py`: calcula hashes, evalúa el gate, resuelve enlaces y genera el HTML.
- `scripts/validate_architecture_presentation.py`: valida estructura, fuentes, hashes, assets, operación offline, vistas y coherencia del gate.
- `scripts/validate_drawio_catalog.py`: valida catálogo, alias, proveedor, XML, páginas, placeholders, bibliotecas y trazabilidad `archiIconId`.
- `scripts/validate_architecture_coherence.py`: audita estructura transversal, IDs/owners, enlaces, snapshot, compromisos, trazabilidad inversa, estados y contradicciones; incluye self-test.

## Artefactos y guías actualizados

- `SKILL.md`: escenario, orden canónico, gates, reglas de diagramación, diseño por contenedor, presentación y checklist previo a entrega.
- `references/plantilla-documento-arquitectura.md`: estructura 00-26, propiedad documental, criterios de cierre y trazabilidad completa.
- `references/guia-gobierno-validacion.md`: checkpoints progresivos y gate `25` reforzado con prometido versus diseñado, estados de evidencia y validación automática.
- `references/cuestionario-linea-base.md`: confirmación de fuentes, gobierno, selección y aprobación.
- `references/guia-clean-code.md`: separación entre criterios arquitectónicos de calidad y operacionalización CI/CD de Vulcano.
- `references/guia-gobierno-validacion.md`: gate condicional para `19.1`, `SEC-xxx`, riesgo residual y handoff.
- `references/guia-arquetipo-solucion.md`, `guia-microfrontends.md` y `guia-presentacion-comite-arquitectura.md`: seguridad y capacidades de entrega sin duplicar DevSecOps.
- `references/diagramas-c4-ejemplos.md`: uso de C4 por nivel y separación del detalle por contenedor.
- `references/diagramas-adicionales-ejemplos.md`: diagramas complementarios y explicaciones de decisiones/interacciones.
- `references/drawio-iconos-nube.md`: separación entre diseño y representación, catálogo curado, referencia neutra, excepciones y validación estricta.
- `references/guia-mcp-diagramacion.md`: somete también los diagramas asistidos por MCP al catálogo y al validador.
- `references/guia-as-is-to-be.md`: brechas, decisiones reemplazadas y transición controlada.
- `references/guia-multi-cloud-deployment.md`: alcance, riesgos, operación y patrones multi-cloud.
- `references/guia-pricing-cloud.md`: fuentes, supuestos, moneda, región y trazabilidad del cálculo.
- `references/guia-terraform-a-diagrama.md`: derivación `recurso IaC → rol → CT → archiIconId → estilo`, sin inferencia inversa.
- `references/plantilla-reporte-costos.md`: correspondencia entre pricing, arquitectura y recomendación.

## Comportamiento por escenario

### Caso A — Greenfield

- Confirma línea base y autoridades.
- Ejecuta QAW, Well-Architected, alternativas, selección, arquetipo, evaluación tecnológica e incertidumbres.
- Impide diseñar antes de cerrar PoC críticas o aceptar formalmente el riesgo.
- Diseña por contenedor significativo y consolida datos, despliegue, patrones, decisiones y riesgos.
- Cuando existen interfaces programáticas, genera y cierra `14.00` y sus contratos ejecutables antes de las secuencias.
- Ejecuta `25`, genera `25.1`, registra aprobación en `26` y solo entonces genera `00`.

### Caso B — AS-IS

- Describe exclusivamente lo observable en código, configuración, pipelines e IaC.
- Omite propuesta, selección y experimentación cuando no existen.
- Genera el arquetipo en estado `Observado`.
- Exige evidencia reproducible para tecnologías, relaciones, patrones y Clean Code.
- Deriva `API-xxx`/operaciones desde especificaciones, rutas/controllers, gateways, schemas, topics, clientes y pruebas, conservando discrepancias como hallazgos.
- Presenta `25.1` como evidencia AS-IS antes de la validación humana.

### Caso C — TO-BE

- Parte de un AS-IS aprobado o actualizado.
- Ejecuta el flujo completo de greenfield anclado a evidencia existente.
- Mantiene transición `AS-IS → TO-BE` por scope, tecnología, decisión y control Clean Code.
- Mantiene compatibilidad, coexistencia, deprecación y migración `AS-IS → TO-BE` de APIs y operaciones.
- Genera análisis de brechas y roadmap de migración.
- Conserva separado el AS-IS aprobado y genera el orquestador TO-BE después de `26`.

## Reglas de calidad y trazabilidad

La cadena mínima resultante es:

`OBJ-xx → QA/FAS → alternativa 09 → selección 10 → ARQ/tecnologías 10.1 → CT-xx → API/operación 14.00 → 14.xx/16.xx → secuencias/despliegue/TP/CC → DA-xxx → revisión 25 → presentación 25.1 → aprobación 26`.

Reglas principales:

- un tema tiene un único documento dueño;
- los documentos derivados resumen y enlazan, no duplican la verdad canónica;
- IDs `CT-xx`, `API-xxx` y `API-xxx-OP-xxx` y sus nombres se mantienen consistentes entre C4, catálogo, contratos, secuencias, datos, despliegue y decisiones;
- cada afirmación material distingue hecho, inferencia, recomendación, decisión y pendiente;
- no se inventan métricas, versiones, costos, responsables, estados ni aprobaciones;
- los hallazgos bloqueantes impiden avanzar al siguiente gate;
- toda excepción tiene motivo, owner y condición o fecha de resolución;
- cada diagrama tiene propósito, dueño y nivel de detalle definido.

## Cambios de compatibilidad y migración

Esta release modifica de forma significativa el orden y la granularidad de los documentos frente a versiones anteriores del skill.

- La numeración previa debe migrarse al orden canónico `00`-`26`.
- `14` y `16` ahora son índices maestros; el detalle vive en archivos `14.xx` y `16.xx` por contenedor.
- `14.00` queda reservado para gobierno/catálogo transversal; los contratos ejecutables heredan el prefijo del `14.xx` owner.
- Los assets de despliegue usan números fijos `17.1`-`17.5` y no comparten la secuencia de contenedores.
- `10.1` se convierte en dueño del arquetipo y baseline tecnológico.
- Hexagonal y CQRS deben retirarse de listas de alternativas macro y ubicarse en el scope de diseño aplicable.
- Las alternativas existentes deben incorporar un mapa común de alcance y justificar agrupación/separación.
- Los documentos existentes deben agregar sus criterios de cierre antes de considerarse completos.
- Una presentación manual previa no sustituye el manifiesto, trazabilidad ni gate de `25.1`.
- Los manifiestos `25.1.1` existentes deben agregar la sección `security`: enlaza `19.1` cuando aplique o registra `No aplica — motivo` con fuente en `19`.
- Los enlaces internos, índices y referencias cruzadas deben actualizarse después de renumerar.

## Validaciones realizadas

- Validación estructural del skill con `quick_validate.py`: **válida**.
- Self-test de `validate_architecture_coherence.py`: **correcto**; acepta una auditoría sintética completa y rechaza un `QA-xx` prometido sin cobertura.
- Validación AST de los scripts de coherencia, generación y presentación: **válida**.
- Prueba del gate de presentación: **correcta**; una auditoría `No apto`/no ejecutada impide `approvalEligible` y `Apto` con validador limpio permite continuar si los demás gates cumplen.
- Validación JSON del esquema y manifiesto de ejemplo: **válida**.
- Validación Draft 2020-12 de `catalogo_iconos_curado.json` contra su esquema: **válida**.
- Cruce de los 50 iconos curados contra `resources/architecture/catalogo_iconos.json`: **0 rutas/shapes faltantes** en Azure, AWS y GCP.
- Validación estricta de la referencia Azure: **correcta**, una página y 11 iconos con `archiIconId` trazable.
- Prueba negativa sobre el antecedente `11.2-Despliegue_Azure_OCTO-HR.drawio`: **rechazo correcto** por dos páginas, imágenes sin trazabilidad, bibliotecas legadas y mezcla de proveedor; el original no fue modificado.
- Validación de sintaxis JavaScript de la plantilla HTML: **válida**.
- Prueba de generación y validación de una presentación borrador: **correcta**.
- Prueba del modo `--strict` frente a una arquitectura con bloqueos: **rechazo correcto**.
- Verificación de whitespace y parches mediante `git diff --check`: **sin errores**.
- Publicación del corte `910cbcd` en `origin/docs/archi-artifacts`: **confirmada**.

## Historial de commits

Las fechas corresponden a la fecha de autor registrada por Git en la zona horaria de Colombia (`UTC-05:00`). La tabla consolida los 12 commits exclusivos de la rama frente a `main@bf25fff`.

| Commit | Fecha y hora | Área | Cambio principal |
|---|---|---|---|
| `94a5aba` | 2026-07-29 16:55:29 | Artefactos | Primera generación de documento, línea base, despliegues y costos |
| `0ecb452` | 2026-07-30 16:20:24 | Artefactos | Regeneración y numeración `00`-`16` de la arquitectura OCTO_HR |
| `d43fe3a` | 2026-07-30 19:16:21 | Artefactos | Alternativas, despliegue, costos, presentación y assets visuales |
| `270a216` | 2026-07-31 15:04:45 | Artefactos | Actualización de presentación/despliegue y generación documental DOCX |
| `6db7ed6` | 2026-08-03 16:02:31 | Skill | Gates de gobierno, alternativas, matriz de decisión, plantilla DOCX y fortalecimiento cloud/costos |
| `7242471` | 2026-08-03 16:06:19 | Skill | Interesados, contexto técnico, estados ADR y fichas mínimas de building blocks |
| `c18fb22` | 2026-08-03 16:35:03 | Skill | ATAM operativo, catálogo de tácticas de calidad y matriz de compra/reutilización |
| `e42d124` | 2026-08-03 16:45:14 | Skill | Diseño detallado y modelo de datos por contenedor significativo; guía Well-Architected |
| `068aa92` | 2026-08-03 20:34:32 | Skill | Clasificación de patrones, Clean Code, fichas detalladas, Mermaid y criterios de cierre |
| `f9bf9e8` | 2026-08-03 20:58:26 | Skill | Alternativas híbridas por alcance y ubicación correcta de Hexagonal/CQRS |
| `8886e8f` | 2026-08-03 21:18:27 | Skill | Arquetipo de solución y baseline tecnológico vivo por proyecto |
| `910cbcd` | 2026-08-03 22:24:03 | Skill | Presentación 25.1 para comité, manifiesto, esquema, plantilla, generador y validador |

## Limitaciones y condiciones

- La aprobación sigue siendo humana y solo se registra en `26`.
- El skill no sustituye talleres, decisiones ni evidencias inexistentes; registra `Missing evidence` cuando corresponde.
- Los artefactos condicionales se omiten sin renumerar los restantes.
- Los diagramas `.drawio` requieren un editor compatible; sus exportaciones SVG/PNG para presentación siguen siendo derivados.
- La presentación requiere Python 3 para el generador/validador y un navegador moderno para la navegación por vistas.
- Los costos continúan siendo estimaciones dependientes de región, fecha, moneda, dimensionamiento y precios del proveedor.
- Un repositorio AS-IS sin código, configuración o IaC suficiente limita el nivel de certeza y debe declarar esa restricción.
- Este archivo documenta la release solicitada; no es una instrucción operativa del skill ni reemplaza `SKILL.md` y sus referencias.

## Ajuste de costos por ambiente — 2026-09-14

Se incorpora `17.4.1-Costos_<Proyecto>.json`, contrato de partidas con evidencia y escenarios, inventario por ambiente en `17`, totales mensuales/únicos por proveedor y asignación de recursos compartidos. El agente remite al contrato; las guías cloud/IA distinguen tarifa pública, contractual, gasto observado y aproximación. Se eliminan multiplicadores universales obligatorios de razonamiento/buffer y promesas fijas de ahorro PTU.

`validate_pricing.py` valida cobertura, fechas, cantidades, duplicación y bloques sincronizados de Markdown/HTML; el validador de coherencia lo integra. Pasaron 15 pruebas sintéticas de pricing y la autoprueba de coherencia. La veracidad comercial de tarifas, completitud de inventario y aprobación financiera permanecen como revisiones explícitas. El presupuesto histórico de OCTO-HR requiere migración al manifiesto y evidencia vigente; no se recalculó en este ajuste.
