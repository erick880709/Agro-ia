# Guía: Gobierno, validación y gates de arquitectura

Esta guía gobierna los puntos de control que separan el análisis, la selección, la reducción de incertidumbre, el diseño detallado y la aprobación. Aplica a los Casos A y C. En Caso B aplica la revisión técnica (`25`), la presentación de evidencia (`25.1`) y la validación (`26`).

## 07 — Resultado del QAW

Ejecuta un Quality Attribute Workshop con los stakeholders relevantes. Si no es posible reunirlos, realiza una ronda asíncrona equivalente; deja explícito que no fue un taller sincrónico.

Genera `07-Resultado-QAW.md` con:

- participantes, roles y autoridad de decisión;
- drivers de negocio revisados;
- escenarios `QA-xx` priorizados por votación o ranking, cada uno trazado a uno o más objetivos `OBJ-xx` de `02`;
- conflictos y trade-offs entre atributos — consulta la matriz de relación de `references/guia-catalogo-tacticas-calidad.md` como punto de partida;
- funcionalidades `FAS-xxx` afectadas;
- decisiones, dudas y acciones pendientes;
- compromisos y lecciones aprendidas del taller, siguiendo el formato de `references/plantilla-documento-arquitectura.md`.

**Mecanismo de votación por defecto** (úsalo salvo que el proyecto ya tenga uno propio): cada participante recibe una cantidad de votos equivalente al 30% de los escenarios consolidados, distribuidos en dos rondas. En la primera ronda cada quien vota los escenarios que le resultan más relevantes; en la segunda se revotan solo los escenarios que quedaron cerca en la primera, hasta obtener un orden de prioridad estable.

## DR-01 — Preparación del dominio

En Casos A/C aplica `references/guia-preparacion-dominio.md` antes de generar `01`. Si el dominio es complejo, Event Storming es obligatorio y el modelo debe estar `validado-dominio`, o en `validacion-parcial` sin hotspots que bloqueen arquitectura. La existencia de archivos `ES-*` no basta: verifica fuentes, participantes, estado y hotspots. Si falta claridad de negocio, devuelve al orquestador hacia `epicureo`; si falta el modelo conductual, hacia `storming`.

**Gate obligatorio:** solo permite continuar con DR-01 `Listo` o `Listo con riesgos`. Registra el contrato en `01` y exige `Hotspots arquitectónicos bloqueantes: Ninguno` y `Handoff pendiente: Ninguno`. Todo riesgo admitido debe tener owner y condición de cierre y quedar resuelto antes de declarar `25` apto. Caso B queda exento mientras sea observación AS-IS; cualquier TO-BE activa Caso C y DR-01.

**Cobertura de atributos (obligatorio):** antes de cerrar la priorización, recorre los 13 atributos de la matriz de relación de `references/guia-catalogo-tacticas-calidad.md`, incluida **Seguridad**, y deja constancia de cada uno en la tabla de cobertura de `07` (ver plantilla) con uno de estos tres estados: **Priorizado** (tiene `QA-xx`), **Considerado y descartado** (se habló del atributo pero no amerita un `QA-xx` propio — indica el motivo), o **No aplica** (el atributo no tiene sentido para este sistema — indica el motivo). Ningún atributo queda fuera de la tabla sin explicación; esto evita que un atributo relevante se pierda simplemente porque nadie lo mencionó en la lluvia de ideas. Seguridad rara vez puede quedar `No aplica`; exige un motivo concreto basado en datos, exposición y amenazas del sistema.

Actualiza `05-Atributos-de-Calidad.md` y `06-Funcionalidades-Significativas.md` con el resultado. En `05`, completa la tabla resumen de atributos y escenarios priorizados y comprueba que orden, prioridad, votos/ranking y `OBJ-xx` coincidan con `07`. No generes alternativas antes de cerrar esta priorización.

## 08 — Well-Architected

Genera `08-Well-Architected.md` después de cerrar `07`. A diferencia del QAW, esta es una revisión **holística**: recorre los 6 pilares de `references/guia-well-architected.md` — ninguno queda sin fila en la matriz de cobertura, hayan sido o no mencionados por un `QA-xx` priorizado.

**Gate de cobertura (obligatorio):** cada pilar queda en uno de tres estados: **Cubierto** (con `PD-xx`/`BP-xxx` derivados de un `QA-xx` o de una recomendación base del pilar), **Considerado y descartado** (se evaluó el pilar pero no amerita prácticas adicionales a las del enfoque ya elegido — indica el motivo), o **No aplica** (con motivo concreto; Seguridad y Confiabilidad rara vez califican para este estado). No marques "No aplica" solo porque `07` no lo priorizó — revisa el pilar igual antes de decidir.

## 10 — Selección de arquitectura

Después de comparar alternativas en `09-Alternativas-de-Solucion.md`, presenta la recomendación y solicita una decisión explícita al responsable identificado en `01-Linea-Base_<Proyecto>.md`.

Genera `10-Seleccion-de-Arquitectura.md` con: configuración recomendada, configuración seleccionada, mapa común de alcance, matriz aprobada que asigna cada capacidad incluida a una agrupación/unidad desplegable, responsable, fecha, condiciones, riesgos aceptados y estado (`Propuesta`, `Seleccionada` o `Rechazada`). El agente puede recomendar, pero nunca marcar `Seleccionada` sin confirmación del usuario o autoridad indicada. No selecciones Hexagonal o CQRS como sustituto de una configuración macro; déjalos para los scopes donde correspondan en `14.xx`/`16.xx`.

**Gate:** no avances a `11`-`14` mientras el estado sea `Propuesta` o `Rechazada`, exista una capacidad incluida sin asignación, un desplegable independiente sin driver verificable, una agrupación que no satisfaga el aislamiento requerido o un bounded context convertido automáticamente en microservicio sin justificación. Si Microfrontends fue candidato, exige comparación con SPA modular, scope/canales, owners y composición aprobados según `references/guia-microfrontends.md`; no aceptes uno por microservicio/pantalla ni una selección basada solo en tecnología. Una recomendación en `09` no equivale a selección humana en `10`.

## 10.1 — Arquetipo de solución

Después de seleccionar `10`, genera `10.1-Arquetipo-de-Solucion_<Proyecto>.md` siguiendo `references/guia-arquetipo-solucion.md`. Debe cubrir todos los scopes aprobados con `ARQ-xxx` y consolidar el baseline tecnológico: tecnología/producto, versión o política, uso, scope/`CT-xx`, estado de adopción, hosting, owner y evidencia/`DA-xxx`.

En Caso B genera el mismo artefacto en estado `Observado` después del escaneo y antes de `14`; `Selección` queda `No aplica — perfil AS-IS`. En Caso C registra `AS-IS → TO-BE`. Mantén `10.1` vivo durante `14`-`21` y actualiza sus `CT-xx`, enlaces y desviaciones.

**Gate de baseline tecnológico:** ninguna tecnología crítica queda `Por decidir`. `Pilotear` debe enlazar `11`, una incertidumbre de `12` y PoC de `13` cuando sea crítica. Una tecnología `No aprobada` obliga a corregir `09`/`10`/`10.1`; una `En retirada` requiere reemplazo, roadmap o riesgo aceptado. Permite borradores de diseño con decisiones no críticas abiertas solo si tienen owner y fecha/condición; resuélvelas antes de `25`.

## 11 — Evaluación de tecnologías emergentes

Genera `11-Evaluacion-Tecnologias-Emergentes.md` solo cuando la alternativa seleccionada use tecnología con madurez, soporte, experiencia interna o comportamiento productivo insuficientemente demostrado.

Evalúa: necesidad que resuelve, madurez, comunidad/soporte, seguridad y cumplimiento, observabilidad, operación, portabilidad, lock-in, habilidades del equipo y salida de contingencia. Cierra cada tecnología con `Adoptar`, `Pilotear` o `Descartar`.

### Evaluación especial de interfaces conversacionales y agentic UI

Cuando exista una `FAS-xxx` de interfaz conversacional, copiloto, tool UI o UI generativa,
clasifica primero la responsabilidad tecnológica. No construyas una matriz plana con productos
que pueden componerse:

| Grupo de decisión | Pregunta | Ejemplos de candidatos a verificar, no recomendación |
|---|---|---|
| Kit/componentes conversacionales | ¿Cómo se realizan composer, messages, tools, threads, feedback y HITL? | assistant-ui, CopilotKit, OpenAI ChatKit, componentes propios |
| Runtime/estado AI UI | ¿Quién gestiona streams, message parts, tools, persistencia, retry/cancel y errores? | Vercel AI SDK UI, runtimes de assistant-ui/CopilotKit/ChatKit, runtime propio |
| Protocolo agente↔UI | ¿Cómo se estandarizan eventos, estado, interrupts, correlación y reanudación? | AG-UI o contrato SSE/WebSocket propio |
| UI generativa declarativa | ¿Cómo describe el agente UI validable usando un catálogo permitido? | A2UI, spec propia o componentes fijos sin UI generativa |

Antes de calificar cada candidato registra fuente oficial, URL, versión/estado, fecha de consulta,
licencia/soporte y deprecaciones/migraciones anunciadas. Verifica compatibilidad con el framework
frontend, backend/agente, transporte, identidad, hosting y baseline de `10.1`; no asumas que una
integración documentada para otro runtime/proveedor aplica al proyecto.

Además de los criterios generales, selecciona los aplicables: cobertura de eventos/estados Iris,
tool rendering y confirmación HITL, threads y reanudación, accesibilidad, customización/Design
System, multimodalidad, seguridad de UI/acciones generadas, contrato y versionado, telemetría,
esfuerzo de adapter, bundle/runtime, testing, portabilidad de backend/modelo y estrategia de salida.
Compara después configuraciones coherentes (`kit + runtime + protocolo [+ generative UI]`) y
documenta solapamientos, dependencias y responsabilidades no cubiertas.

**Gate:** no avances mientras alguna tecnología carezca de decisión. `Pilotear` crea una incertidumbre en `12` y normalmente una PoC en `13`; `Descartar` devuelve el flujo a `09`-`10`.

## 12 — Registro de incertidumbres

Genera siempre `12-Registro-de-Incertidumbres.md` en Casos A y C. Para cada incertidumbre registra: componente, hipótesis, desconocido, impacto, confianza, método de validación, umbral de éxito, responsable y estado.

Clasifica como crítica toda incertidumbre que pueda invalidar la configuración seleccionada o la asignación de un scope, un contrato principal, un atributo `QA-xx`, el presupuesto o la seguridad. Las críticas activan una PoC.

**Gate:** no avances mientras una incertidumbre crítica carezca de método, umbral y responsable de validación.

## 13 — Plan y resultado de PoC

Genera `13-Plan-y-Resultados-PoC.md` cuando exista al menos una incertidumbre crítica. Define antes de ejecutar: hipótesis, alcance, exclusiones, timebox, entorno, datos, métricas, umbrales de éxito y evidencia a conservar. Después registra resultados reproducibles y la decisión `Aprobada`, `Repetir`, `Cambiar arquitectura` o `Riesgo aceptado`.

Para una PoC de interfaz conversacional/agentic UI, congela y enlaza la misma base Iris
`UF/IF/CF/SCR/CMP/ST/ERR/TC` para todas las configuraciones. Incluye, según aplique: event mapping,
first meaningful feedback, completion end-to-end, cancelación, error tardío, desconexión y
reanudación, pérdida de estado, propuesta/confirmación/rechazo de tools, accesibilidad, catálogo
de UI permitido/fallback, instrumentación, esfuerzo de integración y evidencia de lock-in/salida.
Una demo con menos estados o distinto flujo no es una comparación válida.

**Gate:** no avances al diseño detallado (`14`) hasta que cada PoC crítica esté `Aprobada` o el responsable de arquitectura haya aceptado explícitamente el riesgo. Si falla, vuelve a `09` o `10`, según afecte la comparación o la selección.

## Checkpoints progresivos de coherencia

Ejecuta los checkpoints `CP-01` a `CP-04` de `references/guia-auditoria-coherencia-arquitectura.md`. Son controles preventivos, no documentos adicionales:

- `CP-01` después de `07`/`08`: drivers y cobertura;
- `CP-02` después de `10`-`13`: selección, alcance y viabilidad;
- `CP-03` después de `14`-`17`: correspondencia `scope → diseño → datos/API → despliegue`;
- `CP-04` después de `20`-`22`, o `24` en Caso C: reconciliación de decisiones, tácticas, seguridad, riesgos, costos y roadmap.

Registra fecha, revisor, estado, hallazgos y artefactos corregidos en el documento dueño indicado por la guía. Un hallazgo crítico vuelve al primer artefacto afectado y bloquea el siguiente tramo; no se difiere silenciosamente hasta `25`.

## 25 — Revisión técnica

Genera `25-Revision-Tecnica-Arquitectura.md` después de completar los artefactos técnicos. Sigue la estructura obligatoria de `references/guia-auditoria-coherencia-arquitectura.md`: snapshot con hashes, matriz de compromisos, trazabilidad bidireccional, coherencia por dimensión, contradicciones/huérfanos, indicadores, ATAM y dictamen. Verifica trazabilidad `OBJ-xx → QA/FAS → alternativa → selección → ARQ/tecnología → CT-xx → API/operación → 14.xx/16.xx → THR/SEC → DA/TP/CC → prueba o evidencia`, consistencia entre diagramas y texto, seguridad, datos, operación, despliegue, costos, calidad interna, riesgos y pendientes.

**Prometido versus diseñado (gate obligatorio):** inventaría cada objetivo, restricción aplicable, supuesto crítico, `QA-xx`, `FAS-xxx`, condición de selección/PoC, `SEC-xxx`, riesgo aceptado y compromiso de migración. Cada uno debe tener criterio verificable, respuesta concreta, evidencia acorde al escenario, estado y owner. En sentido inverso, cada `ARQ-xxx`, `CT-xx`, `API-xxx`, `TP-xxx`, tecnología crítica y servicio cloud material debe enlazar un driver, restricción o `DA-xxx`. Una promesa crítica sin diseño, una respuesta sin evidencia o un elemento material sin justificación es bloqueante.

**Semántica de evidencia (gate obligatorio):** usa `Definido`, `Diseñado`, `Verificado en diseño`, `Demostrado`, `Implementado`, `Validado operacionalmente`, `Desviado con aprobación` o `No aplica` según la guía. En A/C preimplementación no confundas diseño con implementación; en B no aceptes afirmaciones del estado actual sin evidencia reproducible; en C separa siempre AS-IS y TO-BE.

**Auditoría de criterios de cierre (gate obligatorio):** evalúa contra la tabla de "Criterios de cierre por artefacto" de `references/plantilla-documento-arquitectura.md` todos los artefactos aplicables generados antes de la revisión (`01`-`24`, incluidos `10.1`, `14.00`, `19.1` cuando aplique, y assets). `25` no se incluye a sí mismo en la matriz: se cierra con su checklist local después de completar la auditoría; `26` y `00` se evalúan cuando sean generados. Agrega una fila por archivo real, por lo que cada `14.xx`, `16.xx` y asset `17.1`-`17.5` se evalúa individualmente:

```markdown
### Matriz de criterios de cierre
| Artefacto y versión/hash | Aplicable | Criterios cumplidos | Estado | Evidencia / Hallazgos |
|---|---|---:|---|---|
| 14.01-Diseno-Detallado_CT-01_API.md v1.2 | Sí | 4/4 | Cumple | [enlace al checklist] |
```

Los estados permitidos son `Cumple`, `Cumple con observaciones`, `No cumple` y `No aplica`. `No aplica` exige motivo. Todos los criterios aplicables de la tabla son obligatorios: si falta uno, el estado es `No cumple` y el hallazgo es bloqueante. `Cumple con observaciones` exige los criterios completos y solo admite mejoras adicionales no bloqueantes con responsable y fecha. Para assets sin versión interna usa su SHA-256 como versión revisada. Los checklists locales ayudan a producir el artefacto, pero `25` es la auditoría independiente y no los da por válidos sin revisar evidencia.

**Cobertura de contenedores (gate obligatorio):** valida que todos los contenedores del C4 Nivel 2 estén clasificados, que cada significativo tenga `14.xx`, que cada significativo con estado relevante tenga `16.xx` y que cada omisión esté justificada. Verifica que el mismo `CT-xx` conserve nombre, responsabilidad, contratos y ownership en `14`, `15`, `16`, `17` y `20`. En Microfrontends, solo shell/remotes con build, versión, despliegue y boundary runtime independientes reciben `CT-xx`; los módulos publicados junto con el portal permanecen como componentes. Cualquier falta o inflación del modelo es un hallazgo bloqueante.

**Correspondencia alcance → diseño (gate obligatorio):** compara la matriz seleccionada de `10` contra `14`/`17`. Cada capacidad incluida debe materializarse en el contenedor o agrupación aprobada; cada servicio, worker, función o unidad UI independiente debe conservar el driver que justificó separarlo. Una capacidad perdida, una separación sin driver, un bounded context convertido mecánicamente en servicio, un microfrontend derivado mecánicamente de una pantalla/microservicio o una desviación no aprobada es hallazgo bloqueante. Comprueba en cada `14.xx` que Hexagonal/Capas se evalúen dentro del contenedor y en `14.xx`/`16.xx` que CQRS se limite al scope que demuestra cargas/modelos diferentes.

**Arquetipo y baseline tecnológico (gate obligatorio):** verifica `10 → 10.1 → 14/14.00/16/17/20`. Cada scope de `10` tiene `ARQ-xxx`; cada tecnología está mapeada a su uso y `CT-xx`, con versión/baseline, estado, hosting, owner y evidencia/decisión. Contrasta dependencias, runtime, stores, servicios cloud, protocolos/toolchain de APIs e IaC reales contra `10.1`; una tecnología huérfana, contradicción de versión, piloto sin `11`-`13`, excepción sin aprobador/retiro o afirmación AS-IS sin evidencia es hallazgo bloqueante.

Si existe interfaz conversacional/agentic UI, audita además que kit UI, runtime/estado,
protocolo agente↔UI y UI generativa estén separados o tengan `No aplica` justificado; que la
evaluación no mezcle capas; que la configuración adoptada tenga evidencia de `11`-`13` cuando
corresponda; y que `10.1 → 14.xx frontend → 14.00/contrato → 14.xx backend/agente → 15/20`
coincida con los `SURF/SCR/CMP/ST/ERR/TC` de Iris aplicables.

**Gobierno y contratos de APIs (gate condicional obligatorio):** cuando existan interfaces programáticas, audita `references/guia-gobierno-y-diseno-apis.md` y la cadena `14 → 14.00 → 14.xx → 15/16.xx/18/20`. Comprueba alcance/protocolos, reglas de nomenclatura y compatibilidad, IDs estables `API-xxx`/`API-xxx-OP-xxx`, propósito, owner `CT-xx`/`EXT-xx`, consumidores, exposición, autenticación/autorización, clasificación de datos, estado, SLO y trazabilidad aplicables. Valida cada OpenAPI, AsyncAPI, `.proto`, GraphQL SDL u otro contrato propio requerido con el linter/parser adoptado y contrástalo con catálogo, implementación/evidencia y secuencias; para terceros verifica fuente autoritativa o snapshot no canónico, fecha/versión y detección de cambios. Revisa errores, idempotencia/concurrencia, límites, rate limiting, trazabilidad y lifecycle; en Caso C exige coexistencia, deprecación/migración y rollback para breaking changes. Una API crítica sin owner/consumidor, una operación crítica sin contrato verificable, una contradicción catálogo/contrato, autorización indefinida para datos sensibles o un breaking change sin disposición es hallazgo bloqueante.

**Modelo de amenazas y requisitos de seguridad (gate condicional obligatorio):** evalúa primero la aplicabilidad de `19.1` con `references/guia-modelo-amenazas-y-requisitos-seguridad.md`. Si aplica, comprueba activos, datos, superficies, trust boundaries, método y escala; cada amenaza material `THR-xxx` debe terminar en `SEC-xxx` o aceptación autorizada, y cada `SEC-xxx` debe tener scope, criterio observable, clase de evidencia, owner, estado y trazabilidad a `CT/API/OP/DA/TP`. Los riesgos residuales viven en `21` y las decisiones/excepciones en `20`. Audita que el handoff a Vulcano cubra cada `SEC-xxx` aplicable con estado `Listo`, `Parcial` o `No requiere automatización` justificado. No exijas scanners o pipeline ya implementados en A/C preimplementación: eso pertenece a Vulcano/Bob; sí bloquea una amenaza material sin disposición, un requisito no verificable, un riesgo residual huérfano o una afirmación de implementación sin evidencia.

**Cobertura de atributos y pilares (gate obligatorio):** verifica que `07` clasifique los 13 atributos de `references/guia-catalogo-tacticas-calidad.md`, incluida Seguridad, y que `08` clasifique los 6 pilares de `references/guia-well-architected.md`, cada uno con un estado explícito (`Priorizado`/`Cubierto`, `Considerado y descartado`, o `No aplica`) y motivo cuando corresponda. Un atributo o pilar sin fila en su matriz de cobertura es un hallazgo bloqueante.

**Cobertura de tácticas y patrones (gate obligatorio):** verifica en `18` una fila por cada `QA-xx` priorizado con `TP-xxx` o justificación, la trazabilidad `QA → TP → CT → DA → prueba/evidencia` y una matriz que cubra los cinco tipos de `references/guia-catalogo-patrones.md`: táctica arquitectónica, patrón arquitectónico, patrón de diseño, patrón cloud y patrón IA. Cada tipo queda `Aplicado`, `Considerado y descartado` o `No aplica` con motivo. Comprueba clasificación correcta, fichas completas, validación específica del tipo, consistencia con `09`/`10`/`14.xx`/`15`/`17`/`19`/`20`, parámetros no inventados, riesgos residuales y evidencia de los estados `Implementada`/`Validada`. Valida sintaxis y valor explicativo de cada Mermaid; un diagrama duplicado, decorativo o que no compile es hallazgo, y la ausencia de diagrama es bloqueante solo cuando se cumple alguna condición obligatoria de `references/guia-tacticas-patrones.md`.

**Microfrontends (gate condicional obligatorio):** si está `Seleccionado`, `Implementado` u `Observado`, audita `references/guia-microfrontends.md`: drivers y alternativa SPA modular; scope/owners; shell/composición; correspondencia `10.1 → CT-xx → 14.xx → 15/16/17`; contratos y estado; design system/accesibilidad; autenticación/CSP/requisitos de supply chain; compatibilidad, performance, aislamiento/fallback, telemetría, capacidad de entrega independiente y rollback. Arquitectura define las propiedades y criterios; Vulcano posee herramientas, stages y evidencia continua del pipeline/supply chain. Una unidad declarada independiente que siempre exige release coordinado, un módulo no desplegable modelado como contenedor, ausencia de owner/contrato/rollback o evidencia AS-IS insuficiente es hallazgo bloqueante.

**Clean Code (gate obligatorio):** verifica que `19` defina las reglas `CC-xxx` aplicables con alcance, automatización esperada, umbral o condición de aceptación, responsable, estado y excepción; y que cada `14.xx` con código propio explique su aplicación o justifique `No aplica`. Distingue evidencia de definición (regla, alcance, aceptación y owner) de evidencia de ejecución (código, configuración, análisis, prueba o pipeline). En A/C preimplementación acepta `Definida` cuando la evidencia de definición esté completa, pero no `Aplicada`/`Validada` sin evidencia de ejecución; en B exige evidencia reproducible del repositorio. `archi` define la expectativa; Vulcano decide herramientas, stages y política operativa de fallo. En Caso C audita por separado `AS-IS: <estado> → TO-BE: <estado>`. No inventes métricas ni aceptes `Validada` por declaración. Una regla crítica incumplida, una excepción sin responsable o una afirmación sin la evidencia correspondiente es hallazgo bloqueante; sigue `references/guia-clean-code.md`.

**Análisis ATAM por escenario (obligatorio):** para cada `QA-xx` priorizado, evalúa la arquitectura ya diseñada (no la propuesta en abstracto) siguiendo el formato de "Análisis ATAM por escenario" de `references/plantilla-documento-arquitectura.md` — enfoque arquitectónico, decisiones que lo soportan, punto de sensibilidad, punto de equilibrio (trade-off), riesgo y razonamiento. Este paso es lo que distingue la revisión técnica de un simple chequeo de completitud: valida que el diseño de `14`-`19` realmente sostenga los atributos priorizados en `07`, no solo que existan los diagramas.

**Validación automática (gate obligatorio):** después de completar `25`, ejecuta `scripts/validate_architecture_coherence.py <directorio> --scenario <A|B|C> --strict`. Registra comando, fecha, salida y versión/hash del script en `25`. El validador comprueba integridad estructural y trazabilidad; el revisor conserva la responsabilidad sobre suficiencia, trade-offs y ATAM. Cualquier error deja el dictamen `No apto`.

Registra cada hallazgo con severidad, artefacto afectado, responsable, disposición y evidencia de cierre. Incluye compromisos (responsable y fecha de seguimiento) para los hallazgos que no bloquean pero requieren acción, y lecciones aprendidas del proceso de revisión. No presentes a aprobación mientras existan hallazgos bloqueantes abiertos ni artefactos aplicables en `No cumple`.

## 25.1 — Presentación para Comité de Arquitectura

Después de cerrar la matriz y el análisis ATAM de `25`, genera `25.1.1-Manifiesto-Presentacion_<Proyecto>.json` y `25.1-Presentacion-Comite-Arquitectura_<Proyecto>.html` siguiendo `references/guia-presentacion-comite-arquitectura.md`. Resume la decisión solicitada y la evidencia ya revisada; no copies contenido como una nueva verdad canónica ni sustituyas los documentos dueños.

La presentación incluye tres vistas en el mismo HTML (`Ejecutiva`, `Arquitectura`, `Completa`) y demuestra el trabajo realizado: drivers/QAW, alternativas y sensibilidad, selección y scope, arquetipo/baseline, incertidumbres/PoC, C4 y detalle por contenedor significativo, flujos, datos, cloud/despliegue, tácticas/patrones/Clean Code, amenazas y requisitos `SEC-xxx` materiales cuando aplique, decisiones, ATAM, riesgos, costos y roadmap aplicable. Cada afirmación material enlaza la fuente y su hash; cada diagrama es un asset local trazado a su dueño.

**Gate de presentación:** `approvalEligible=true` solo cuando `25` esté en `Cumple` o `Cumple con observaciones`, no haya hallazgos bloqueantes ni conflictos materiales abiertos y la selección de `10` sea humana en Casos A/C. Antes de ese punto solo se permite un borrador con watermark `BORRADOR — NO APTO PARA APROBACIÓN`. Ejecuta el generador con `--strict` y después `scripts/validate_architecture_presentation.py` para una sesión de aprobación.

Agrega al final de `25` una subsección `Validación de 25.1` con fecha, versión, SHA-256 del manifiesto y HTML, resultado del validador, errores/advertencias y disposición. Esto no reabre la auditoría de `01`-`24`; sí obliga a regenerar `25.1` cuando cambie una fuente.

## 26 — Validación y aprobación

Presenta al cliente o Comité de Arquitectura `25.1` y los artefactos fuente enlazados solo cuando la matriz de `25` muestre `Cumple` o `Cumple con observaciones` no bloqueantes, y el validador de `25.1` no reporte errores. Genera `26-Validacion-y-Aprobacion.md` con participantes, fecha, alcance de la revisión, hashes/versiones de `25.1` y fuentes revisadas, observaciones, condiciones, compromisos (responsable y fecha de seguimiento), lecciones aprendidas y estado (`Pendiente`, `Aprobada`, `Aprobada con condiciones` o `Rechazada`). El agente nunca se autoaprueba.

Si se rechaza o cambia una fuente después de `25`, vuelve al primer artefacto afectado:

- drivers o calidad: `02`-`08`;
- alternativa o viabilidad: `09`-`13`;
- diseño: `14`-`24`.

Actualiza los artefactos en sitio, repite el checkpoint correspondiente, actualiza snapshot, matrices, ATAM, contradicciones y dictamen de `25`, reejecuta el validador completo, regenera/revalida `25.1`, actualiza `26` y conserva el historial. Genera el orquestador `00` únicamente después de `Aprobada` o `Aprobada con condiciones`; en este último caso, muestra las condiciones abiertas en el resumen ejecutivo.
