# Guía: Arquetipo de solución por proyecto

Usa esta guía para generar `10.1-Arquetipo-de-Solucion_<Proyecto>.md`. El artefacto es la ficha técnica canónica del proyecto: clasifica la solución, identifica los arquetipos implementables que deben construirse como plantillas/scaffolds y consolida el baseline tecnológico seleccionado u observado, con alcance, ownership, estado y evidencia. No reemplaza contexto, decisiones, C4, datos o despliegue; los resume y enlaza.

`05.04.06-Analysis-Archetypes.md` es el ejemplo estructural de referencia cuando exista en el repositorio. Úsalo para calibrar formato, profundidad y orientación implementable: definición, inventario, análisis detallado, árboles de carpetas, patrones incorporados, componentes compartidos, convenciones, prioridad y relación con legado. Es solo un ejemplo: no copies sus nombres, AWS, Lambda, Angular, versiones, umbrales, scripts ni decisiones. Todo contenido del proyecto se deriva de `01`, `02`, `05`-`10`, evidencia AS-IS y decisiones confirmadas.

## Contenido

1. Propiedad y momento de generación
2. Aplicación por escenario
3. Estructura obligatoria
4. Clasificación del arquetipo
5. Arquetipos identificados
6. Análisis detallado por arquetipo implementable
7. Baseline tecnológico
8. Building blocks, componentes compartidos e integraciones
9. Convenciones transversales y contrato de repositorio
10. Datos, seguridad y operación
11. Patrones, desviaciones, legado y evolución
12. Prioridad de construcción
13. Estados, evidencia y gates
14. Criterios de cierre

## 1. Propiedad y momento de generación

`10.1` posee la composición de arquetipos, la especificación de los scaffolds requeridos y el inventario tecnológico canónico del proyecto. Su relación con los demás artefactos es:

| Artefacto | Responsabilidad |
|---|---|
| `01` | Fuentes, stack actual/condicionantes y vacíos de línea base |
| `02` | Contexto, propósito, alcance y stakeholders completos |
| `09` | Tecnologías y configuraciones candidatas por alternativa |
| `10` | Configuración seleccionada y asignación aprobada por scope |
| `10.1` | Perfil técnico seleccionado/observado, arquetipos implementables, estructura de scaffold y baseline tecnológico vigente |
| `11`-`13` | Madurez, incertidumbre y PoC de tecnologías que requieren validación |
| `14`-`17` | Diseño lógico, datos y despliegue que materializan el baseline |
| `18`-`21` | Patrones/tácticas, dimensiones, decisiones y riesgos detallados |
| `25` | Auditoría independiente de consistencia y evidencia |

En A/C inicia después de la selección humana de `10`; en B inicia después del escaneo tecnológico. Permanece vivo durante el diseño y se revalida en `25`. Si cambia una tecnología, actualiza `10.1` y la `DA-xxx`/evidencia correspondiente antes de cerrar artefactos dependientes.

## 2. Aplicación por escenario

- **Caso A — Greenfield:** estado de arquetipo `Seleccionado`. Registra baseline objetivo y criterios de aceptación; no marques implementación o validación sin evidencia.
- **Caso B — AS-IS:** estado `Observado`. Deriva tecnologías, versiones, dependencias y hosting de código/configuración/IaC; usa `Missing evidence` donde no pueda verificarse. `10` puede no existir y se registra `Selección: No aplica — perfil AS-IS`.
- **Caso C — TO-BE:** registra por scope y tecnología `AS-IS → TO-BE`, qué se conserva/migra/retira y la acción relacionada de `23`/`24`. El estado objetivo requiere selección de `10`.

Un proyecto puede combinar varios subarquetipos. No fuerces una sola etiqueta cuando el core transaccional, notificaciones, analítica e IA tienen workloads diferentes.

## 3. Estructura obligatoria

Genera estas secciones en orden. Los títulos indicados son canónicos porque el validador los usa como contrato:

1. Identificación, versión, estado y responsables.
2. `## Definición y propósito de los arquetipos`.
3. `## Perfil detallado del proyecto`.
4. Clasificación del arquetipo principal `ARQ-001`.
5. `## Arquetipos identificados`, con inventario de los scaffolds requeridos.
6. `## Análisis detallado por arquetipo`, con una ficha `### ARQ-xxx — <Nombre>` por cada arquetipo implementable.
7. `## Baseline tecnológico canónico`.
8. `## Componentes compartidos e integraciones`.
9. `## Convenciones transversales`.
10. `## Datos, seguridad y operación`.
11. `## Patrones, desviaciones, legado y evolución`.
12. `## Prioridad de construcción`.
13. `## Decisiones de framework y baseline`.
14. `## Matriz de trazabilidad`.
15. `## Criterios de cierre`.

Usa IDs estables `ARQ-001`, `ARQ-002`, etc. `ARQ-001` representa la composición principal; los siguientes identifican subarquetipos significativos. No reasignes IDs en revisiones posteriores.

## 4. Clasificación del arquetipo

Incluye una ficha autónoma, pero enlaza al dueño del detalle:

```markdown
## ARQ-001 — [Nombre del arquetipo principal]
| Dimensión | Clasificación | Justificación / Evidencia |
|---|---|---|
| Canal | Web / API / Móvil / Batch / Mixto | [02/FAS] |
| Composición frontend | N/A / SPA modular / Apps por ruta / Microfrontends runtime / Server-side-edge / Híbrida | [09/10/guía Microfrontends] |
| Workload | Transaccional / Integración / Datos / IA / Mixto | [drivers] |
| Modo de IA | N/A / Inferencia puntual / Copiloto / Workflow determinístico con IA / Agentic | [01/10/evidencia] |
| Topología agentic | N/A / Agente único / Multiagente | [agentes, herramientas, memoria y comunicación] |
| Descomposición | Consolidada / Híbrida / Distribuida | [09/10] |
| Comunicación | Síncrona / Event-driven / Batch / Mixta | [15/18] |
| Datos | Relacional / Documento / Analítico / Vectorial / Mixto | [16] |
| Hosting | Cloud / On-premise / Híbrido / Multi-cloud | [17] |
| Tenancy | Single-tenant / Multi-tenant / Mixto | [decisión] |
| Criticidad | Baja / Media / Alta / Misión crítica | [QA/riesgo] |
```

No uses nombres de productos como nombre del arquetipo. Nombra la clase de solución, por ejemplo `Plataforma híbrida transaccional y orientada a eventos`.

En `## Perfil detallado del proyecto` declara siempre los marcadores canónicos que usa la auditoría:

```markdown
**Aplicabilidad agentic:** Sí — [evidencia/decisión y alcance]
**Topología agentic:** Agente único / Multiagente
```

o:

```markdown
**Aplicabilidad agentic:** No — [motivo verificable]
**Topología agentic:** N/A
```

Marca `Sí` cuando al menos un componente planifique o itere para alcanzar una meta, seleccione o invoque herramientas, conserve memoria que influya decisiones, ejecute acciones con efecto externo o delegue/se comunique con otros agentes. Una inferencia puntual o un workflow totalmente determinístico que solo llama a un modelo no basta por sí solo. Si es `Sí`, `19.1` es obligatorio y adopta `OWASP Top 10 for Agentic Applications 2026` como baseline de riesgos; no lo presentes como certificación.

## 5. Arquetipos identificados

Mapea todos los scopes incluidos de `10` o detectados en B. Diferencia la composición principal `ARQ-001` de los arquetipos implementables: estos últimos son bases clonables o generables para iniciar repositorios, contenedores o unidades de entrega homogéneas.

```markdown
## Arquetipos identificados
| `ARQ-xxx` | Nombre del arquetipo implementable | Modelo de ejecución/entrega | Scopes que lo usan | Instancias previstas | Repositorio/paquete plantilla | Owner | Estado/evidencia |
|---|---|---|---|---:|---|---|---|
| ARQ-002 | `<proyecto>-archetype-api` | API en contenedor | Nómina, Ausencias | 2 | Por crear | Equipo Plataforma | Seleccionado en 10 |
| ARQ-003 | `<proyecto>-archetype-worker` | Worker asíncrono | Notificaciones | 1 | Por crear | Equipo Plataforma | Seleccionado en 10 |
```

Antes de `14`, el mapeo a `CT-xx` puede ser `Pendiente de diseño`; actualízalo cuando exista el inventario C4. Toda capacidad incluida debe quedar cubierta. Un scope puede usar varios arquetipos si el motivo es explícito. No crees un arquetipo por bounded context, pantalla o contenedor: agrupa instancias que realmente comparten estructura, runtime, convenciones y mecanismo de entrega.

## 6. Análisis detallado por arquetipo implementable

Después del inventario, genera una ficha por cada `ARQ-xxx` implementable usando un encabezado `### ARQ-xxx — <Nombre concreto del scaffold>`. La ficha debe ser suficiente para que Builder o un equipo cree la plantilla sin reinterpretar la arquitectura, pero no debe incluir código productivo completo.

Cada ficha contiene, en este orden, las siguientes subsecciones canónicas:

1. `#### Scopes y componentes objetivo`: capacidades, `FAS/QA`, instancias previstas y exclusiones.
2. `#### Propósito y cuándo usarlo`: problema que estandariza y criterio para elegirlo frente a otro arquetipo.
3. `#### Características principales`: runtime, framework, entrada/triggers, persistencia, mensajería, configuración, observabilidad, pruebas, empaquetado y despliegue; todo trazado al baseline o marcado `Por decidir`.
4. `#### Estructura de carpetas propuesta`: árbol en bloque de código con archivos/directorios principales y comentarios breves. Debe reflejar lenguaje y herramientas reales del proyecto, separar dominio/aplicación/infraestructura solo cuando el patrón esté seleccionado y mostrar pruebas, configuración, scripts e IaC aplicables. Para un arquetipo sin repositorio de código, escribe `N/A — <motivo>` y describe la estructura de configuración o paquete que corresponda.
5. `#### Patrones y controles incorporados`: `TP-xxx`, `CC-xxx`, seguridad, resiliencia, errores, contratos, telemetría y criterios verificables que el scaffold trae por defecto.
6. `#### Contrato de desarrollo`: comandos o scripts mínimos para build, ejecución local, lint/format, type-check, pruebas unitarias/integración/contrato y empaquetado. No inventes comandos: usa convenciones confirmadas o deja `Por decidir` con owner.
7. `#### Configuración y secretos`: archivos de ejemplo permitidos, variables/configuración requerida y prohibición de credenciales reales.
8. `#### Diferencias y reutilización`: comparación con el arquetipo vigente/legado o con el arquetipo base más cercano; indica qué se reutiliza, adapta o retira. Si no existe antecedente, declara `No existe baseline previo` con evidencia.
9. `#### Criterios de aceptación del scaffold`: prueba de generación, build limpio, tests, análisis estático, ejecución local, artefacto empaquetado y trazabilidad a decisiones aplicables.

No copies el árbol del ejemplo. Derívalo del stack seleccionado y conserva consistencia entre arquetipos relacionados; una variante debe declarar explícitamente qué hereda del arquetipo base y solo detallar sus diferencias.

Para cada arquetipo agentic, las subsecciones anteriores deben explicar además:

- runtime del agente y separación respecto del modelo, herramientas y sistemas destino;
- catálogo de herramientas con schemas, identidad efectiva, permisos, límites, idempotencia y efectos externos;
- memoria/contexto con procedencia, clasificación, TTL/retención, aislamiento, invalidación y protección contra envenenamiento;
- nivel de autonomía, presupuesto, límites de iteración/tiempo/costo, condiciones de terminación y principio de mínima agencia;
- decisiones que requieren aprobación humana, información presentada al revisor y autoridad de override;
- observabilidad de objetivo, plan, pasos, herramientas, resultados, decisiones y correlación, sin exponer secretos ni razonamiento interno sensible;
- contención, fallback seguro, revocación, pausa y kill switch;
- para multiagente, identidad por agente, delegación, autenticidad/integridad de mensajes, autorización A2A, prevención de loops y aislamiento de fallos.

Enlaza estos controles con `TP-xxx`, `THR-xxx`, `SEC-xxx` y la matriz `ASI01`-`ASI10` de `19.1`; `10.1` describe lo que el scaffold debe incorporar, mientras `19.1` posee el análisis de amenazas.

## 7. Baseline tecnológico

Incluye una fila por tecnología, producto, runtime, framework, store o plataforma con impacto en construcción u operación:

```markdown
| Capa | Tecnología/producto | Versión/baseline | Uso | Scope/`CT-xx` | Estado de adopción | Hosting | Owner | Evidencia/`DA-xxx` |
|---|---|---|---|---|---|---|---|---|
| Backend | .NET | 10.x | APIs y dominio | Nómina / CT-02 | Adoptada | Contenedor | Backend | DA-004 |
| Mensajería | Azure Service Bus | SKU por decidir | Eventos | CT-02/CT-03 | Pilotear | Azure | Plataforma | 11/12/13 |
```

Estados tecnológicos permitidos: `Adoptada`, `Pilotear`, `Restringida`, `En retirada`, `No aprobada`, `Por decidir`. `Missing evidence` vive en la columna de evidencia, no como estado.

Mapea el resultado de `11` así: `Adoptar → Adoptada`, `Pilotear → Pilotear`, `Descartar → No aprobada`. Conserva el enlace y fecha de evaluación.

- Registra versión exacta, rango soportado o política de actualización; no inventes una versión.
- `Pilotear` obliga a enlazar `11`, incertidumbre de `12` y PoC de `13` cuando sea crítica.
- `Por decidir` incluye responsable, fecha/condición y alternativas; una decisión crítica abierta bloquea diseño detallado.
- En C agrega estado/baseline `AS-IS → TO-BE` o filas separadas claramente enlazadas.
- No declares `Adoptada` por preferencia del agente: exige selección, estándar organizacional o evidencia AS-IS.
- Cuando algún scope tenga workload `Datos`/analítica o incluya dashboards, reportería o KPIs (`FAS-xxx` relacionado), registra explícitamente la capa de visualización con su librería/motor de gráficos concreto (no solo el framework de UI general); si aún no hay selección, dilo como `Por decidir` con owner y fecha en vez de omitir la fila.
- Cuando exista una experiencia conversacional o agentic UI, no la escondas bajo una sola fila
  `Frontend | React/Angular/...`. Registra por separado las capas aplicables o una fila explícita
  `No aplica — <motivo>` en la decisión correspondiente:
    - **Kit/componentes de UI conversacional:** composer, mensajes, tools, threads, feedback y HITL;
    - **Runtime/estado AI UI:** streaming, message parts, tools, persistencia, retry/cancel y errores;
    - **Protocolo agente↔UI:** eventos, estado, correlación, interrupts, transporte y reanudación;
    - **UI generativa declarativa/renderer:** schema, catálogo permitido, data binding, acciones,
      validación y fallback.
- assistant-ui, Vercel AI SDK UI, AG-UI, A2UI, OpenAI ChatKit y CopilotKit son ejemplos de
  candidatos de esas capas, no un baseline recomendado. Antes de registrarlos verifica fuente
  oficial, versión/estado, fecha, compatibilidad, licencia/soporte y deprecaciones. Una solución
  puede componer varios; el baseline debe hacer visible qué responsabilidad cubre cada uno.

Ejemplo de filas cuando las capas aplican, usando únicamente valores ya seleccionados o
marcándolos `Por decidir`/`Pilotear`:

```markdown
| Agent UI | <kit/componentes> | <baseline> | Composer, mensajes, tools, threads y HITL | CT-01 | <estado> | Cliente | Frontend | <DA/11-13> |
| AI UI runtime | <runtime/estado> | <baseline> | Stream, message parts, persistencia y retry/cancel | CT-01 | <estado> | Cliente/BFF | Frontend | <DA/11-13> |
| Agent-UI protocol | <protocolo o contrato propio> | <versión> | Eventos, estado, correlación y reanudación | CT-01/CT-04 | <estado> | Red interna | Frontend+Agente | <DA/14.00> |
| Generative UI | <spec/renderer o No aplica> | <versión> | UI declarativa sobre catálogo permitido | CT-01/CT-04 | <estado> | Cliente/Agente | Frontend+Agente | <DA/11-13> |
```

- Si aplica Microfrontends, registra por shell/remote framework/runtime, baseline compatible, mecanismo de composición, unidad de build/despliegue, capacidad de entrega independiente, hosting/CDN, owner y estado. Enlaza pipeline AS-IS o Vulcano cuando exista; no lo diseñes aquí. La diversidad tecnológica requiere driver y `DA-xxx`; no la presentes como beneficio por sí sola.

## 8. Componentes compartidos e integraciones

Registra building blocks compartidos: identidad, gateway/BFF, mensajería, auditoría, secretos, configuración, observabilidad, librerías/plataformas corporativas y componentes reutilizables. Para cada librería o paquete compartido indica propósito, consumidores, publicación/versionado, ownership, compatibilidad y estructura interna resumida. Evita un módulo `shared` genérico sin fronteras ni owner.

Cuando el frontend sea distribuido, agrega una matriz enlazada a `references/guia-microfrontends.md`:

```markdown
| Canal/scope | Subarquetipo UI | Shell/compositor | Unidad build/despliegue | Composición | Design system/estado compartido | Owner | `CT-xx`/evidencia |
|---|---|---|---|---|---|---|---|
```

Incluye identidad/sesión, telemetría y contratos compartidos. Un BFF se registra por canal/capacidad solo si adaptación, seguridad o agregación lo justifican; no asignes uno automáticamente a cada microfrontend.

Para interfaces conversacionales/agentic UI registra también los adaptadores entre kit/runtime,
protocolo y backend agente. Declara consumidores, responsabilidad, versionado, mapping de eventos,
compatibilidad y fallback. Si la implementación consume un contrato propio en vez de AG-UI u otro
estándar, nómbralo y enlaza su contrato ejecutable; “cliente de chat” no es suficiente como
building block.

Para cada integración resume sistema, dirección, protocolo/formato, autenticación, frecuencia/SLA, manejo de error y owner. Enlaza `02`, `14.00`, `14.xx` y `15`; no copies nomenclatura, catálogos ni contratos completos. Cuando existan interfaces programáticas, `14.00-Gobierno-y-Catalogo-Inicial-de-APIs_<Proyecto>.md` es el dueño del gobierno y los IDs `API-xxx`/`API-xxx-OP-xxx`.

## 9. Convenciones transversales y contrato de repositorio

Documenta las convenciones que todos los arquetipos materializan, siempre derivadas de estándares o decisiones del proyecto:

- nombres de repositorios, paquetes, módulos y namespaces;
- estructura mínima de README, configuración, `.env.example` sin secretos e IaC;
- lenguaje/runtime soportado y política de versiones;
- formato, lint, type-check/análisis estático y hooks locales;
- estrategia y ubicación de pruebas, cobertura o quality gates solo cuando estén confirmados;
- logging, correlación, manejo de errores, configuración y feature flags;
- scripts/comandos estándar de build, desarrollo local, pruebas, empaquetado y validación;
- publicación/versionado de plantillas y librerías compartidas.

Incluye tablas o bloques de comandos concretos cuando exista evidencia. No conviertas preferencias del agente ni valores del ejemplo en estándar del proyecto.

## 10. Datos, seguridad y operación

Resume y enlaza:

- fuentes de verdad, stores por scope, consistencia, clasificación, PII, retención, backup/recuperación, analítica y vector stores;
- identidad, autorización, fronteras de confianza, cifrado, secretos, auditoría, amenazas `THR-xxx`, requisitos `SEC-xxx`, supply chain y regulación;
- capacidades requeridas de repositorio/build/entrega, dependencias, IaC, ambientes, pruebas, reglas `CC-xxx`, observabilidad, runbooks, soporte, RTO/RPO y continuidad; enlaza Vulcano para la estrategia CI/CD y DevSecOps.

Cada afirmación significativa apunta al artefacto dueño o evidencia. Si aún no existe el documento de detalle, registra el criterio objetivo y el enlace pendiente con responsable.

Cuando `Aplicabilidad agentic: Sí`, identifica expresamente runtime, modelos, prompts/policies, skills/plugins, herramientas/MCP, identidades, memoria/contexto, stores, sistemas destino, supervisores humanos y canales A2A. Declara su procedencia/owner, trust boundary, privilegio y efecto; enlaza la disposición de `ASI01`-`ASI10` en `19.1`.

## 11. Patrones, desviaciones, legado y evolución

Incluye un resumen enlazado de `TP-xxx`, `DA-xxx`, `QA-xx` y riesgos que definen el arquetipo; no dupliques sus fichas.

Registra desviaciones:

```markdown
| Baseline/estándar | Desviación | Motivo | Riesgo | Aprobador | Condición/fecha de retiro | Enlace |
|---|---|---|---|---|---|---|
```

Toda excepción tiene owner y disposición. En C agrega qué se conserva, migra o retira, compatibilidad y fase de `24`. Tecnologías `En retirada` deben tener reemplazo o riesgo aceptado.

Agrega una subsección `### Relación con arquetipos existentes` que inventarie plantillas, repositorios o convenciones vigentes. Compara estructura, stack, autenticación, datos, eventos, pruebas, observabilidad y entrega; concluye para cada elemento `Reutilizar`, `Adaptar`, `Retirar` o `No aplica`, con evidencia. No desacredites un legado sin inspeccionarlo.

## 12. Prioridad de construcción

Ordena los arquetipos y componentes compartidos por dependencia y valor habilitador:

```markdown
| Prioridad | `ARQ-xxx` / componente | Dependencias | Justificación | Responsable | Hito/condición de inicio | Estado |
|---:|---|---|---|---|---|---|
```

No inventes sprints ni fechas. Usa hitos confirmados o condiciones de inicio. Una variante no se construye antes que su base y una librería compartida debe tener un consumidor real.

Incluye `## Decisiones de framework y baseline` después de la prioridad. Resume únicamente decisiones que eliminan ambigüedad para construir los scaffolds —framework, runtime, build, persistencia, composición o empaquetado— y enlaza sus `DA-xxx`; el razonamiento completo sigue viviendo en `20`.

## 13. Estados, evidencia y gates

Estados del arquetipo: `Propuesto`, `Seleccionado`, `Observado`, `Validado`, `Obsoleto`.

No confundas dos estados distintos:

- **Estado del arquetipo:** ciclo de vida técnico anterior.
- **Estado de cierre del artefacto:** `Cumple`, `Cumple con observaciones`, `No cumple` o `No aplica`, según la plantilla general.

Un arquetipo puede estar `Seleccionado` y su documento en `No cumple` porque faltan versiones, owners, evidencia o disposiciones. `Cumple con observaciones` exige todos los criterios aplicables completos y solo admite mejoras no bloqueantes; no lo uses para encubrir campos requeridos pendientes. Un valor `Pendiente de diseño` satisface el gate inicial únicamente cuando es permitido por esta guía y tiene owner y momento de actualización.

- `Seleccionado` exige `10` aprobado en A/C.
- `Observado` exige evidencia AS-IS por cada afirmación material.
- `Validado` exige consistencia comprobada con `14`-`21` y auditoría de `25`; no se usa al generar inicialmente `10.1`.
- `Obsoleto` conserva sucesor y fecha.

Antes de iniciar diseño detallado, cada tecnología crítica queda `Adoptada`, `Restringida`, `En retirada` con plan, o `Pilotear` con validación gobernada. `Por decidir` crítico bloquea. Tecnologías no críticas pueden permanecer abiertas con owner/fecha durante borradores, pero deben resolverse antes de `25`.

## 14. Criterios de cierre

### Gate inicial — antes de `11`/`14`

`10.1` puede cerrar su baseline inicial cuando:

- identifica proyecto, `ARQ-xxx`, estado, versión, owner y fecha;
- describe propósito, alcance, criticidad, datos/regulación y operación sin contradecir `02`;
- cubre cada capacidad incluida con un subarquetipo y forma desplegable;
- inventaría los arquetipos implementables y cada uno tiene ficha detallada con scopes, características, estructura propuesta, patrones, contrato de desarrollo, configuración, relación con baseline y criterios de aceptación;
- cada tecnología tiene capa, versión/baseline, uso, scope, estado, hosting, owner y evidencia/decisión;
- si existe experiencia conversacional/agentic UI, el baseline separa kit UI, runtime/estado,
  protocolo agente↔UI y UI generativa, o justifica `No aplica`; cada candidato en piloto enlaza
  `11`-`13` y cada adopción enlaza una decisión de `20`;
- cada `Pilotear` o decisión crítica abierta tiene responsable y acción explícita para generar/enlazar `11`-`13`;
- componentes compartidos, integraciones, convenciones transversales, datos, seguridad, entrega y operación tienen resumen y enlaces;
- declara `Aplicabilidad agentic` y `Topología agentic` con motivo/evidencia; si aplica, cada arquetipo agentic cubre mínima agencia, herramientas, identidad, memoria, límites, supervisión, observabilidad, contención/kill switch y, cuando corresponda, comunicación multiagente, con enlaces pendientes gobernados a `19.1`;
- registra prioridad/dependencias de construcción y relación `Reutilizar/Adaptar/Retirar/No aplica` con arquetipos existentes;
- si aplica Microfrontends, la matriz frontend identifica subarquetipo, shell, owners, unidades, composición, baseline, capacidad de entrega/hosting y estado; si existe pipeline AS-IS/Vulcano lo enlaza, y si se descartó `09` conserva el motivo;
- excepciones tienen motivo, riesgo, aprobador y condición de retiro;
- coincide con `10`; los `CT-xx` y enlaces de diseño aún inexistentes quedan `Pendiente de diseño` con owner, sin considerarse incumplimiento inicial;
- en B toda afirmación material disponible tiene evidencia y en C separa AS-IS/TO-BE;
- no duplica diagramas, contratos, decisiones o fichas cuyo dueño sea otro artefacto.

### Revalidación final — en `25`

Antes de aprobar, actualiza `CT-xx` y enlaces definitivos; resuelve tecnologías `Por decidir`; reemplaza acciones de piloto por evidencia de `11`-`13`; y comprueba coincidencia con `14`, `16`, `17`, `18`, `19.1` cuando aplique, `20` y `21`. Si existe interfaz conversacional/agentic UI, verifica además que cada capa del baseline tenga mapping en el `14.xx` frontend y, para protocolo/UI generativa, contrato versionado en `14.00`/`14.xx.y`; las pruebas deben enlazar los requisitos Iris aplicables. Si la solución es agentic, verifica que la topología y los controles del arquetipo coincidan con los diez estados `ASI01`-`ASI10`, sus `THR/SEC/TP/DA` y riesgos residuales. Para Microfrontends verifica que cada unidad declarada independiente tenga owner, build/despliegue/rollback y correspondencia `CT-xx`, sin confundir módulos compilados junto con el shell; el pipeline detallado se valida en Vulcano o como evidencia AS-IS. Cualquier contradicción, tecnología huérfana o excepción sin disposición deja `10.1` en `No cumple`.
