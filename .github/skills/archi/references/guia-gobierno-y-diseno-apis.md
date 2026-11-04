# Guía: Gobierno, diseño y catálogo inicial de APIs

Aplica cuando el sistema expone o consume interfaces programáticas REST/HTTP, eventos, gRPC, GraphQL, webhooks u otros contratos entre unidades desplegables o con terceros. Genera `14.00-Gobierno-y-Catalogo-Inicial-de-APIs_<Proyecto>.md` como documento transversal del proyecto. Si no existe ninguna interfaz programática, no generes un archivo vacío: registra `No aplica` y el motivo en `14-Vistas-C4.md`.

## Contenido

1. [Propiedad y límites](#1-propiedad-y-límites)
2. [Orden de generación](#2-orden-de-generación)
3. [Identificadores y ciclo de vida](#3-identificadores-y-ciclo-de-vida)
4. [Contenido obligatorio de `14.00`](#4-contenido-obligatorio-de-1400)
5. [Nomenclatura](#5-nomenclatura)
6. [Buenas prácticas de diseño](#6-buenas-prácticas-de-diseño)
   - [Protocolos agente↔UI y UI generativa](#61-protocolos-agenteui-y-ui-generativa)
7. [Seguridad, resiliencia y operación](#7-seguridad-resiliencia-y-operación)
8. [Contratos ejecutables](#8-contratos-ejecutables)
8.1. [Mapeo profundo de integraciones externas](#81-mapeo-profundo-de-integraciones-externas)
9. [Aplicación por escenario](#9-aplicación-por-escenario)
10. [Criterios de cierre](#10-criterios-de-cierre)

## 1. Propiedad y límites

`14.00` es el dueño de:

- alcance y clasificación de las APIs del proyecto;
- estándar de nomenclatura elegido y desviaciones aprobadas;
- políticas transversales de diseño, seguridad, compatibilidad, observabilidad y ciclo de vida;
- catálogo canónico de `API-xxx` y listado inicial de operaciones `API-xxx-OP-xxx`;
- trazabilidad entre API, operación, consumidor, owner, `CT-xx`, `FAS-xxx`, `QA-xx`, secuencia, contrato y decisión.

No copies en `14.00` esquemas completos de solicitudes/respuestas ni el diseño interno de los contenedores. Distribuye responsabilidades así:

| Artefacto | Responsabilidad |
|---|---|
| `10.1` | Tecnologías, frameworks, gateways y toolchain del baseline |
| `14` | Contenedores, relaciones e inventario global |
| `14.00` | Gobierno transversal e inventario canónico de APIs/operaciones |
| `14.xx` | Cómo el `CT-xx` implementa o consume los contratos y aplica las reglas |
| `14.xx.y` | Contrato ejecutable OpenAPI, AsyncAPI, Protobuf o GraphQL propiedad del contenedor |
| `15` | Uso de `API-xxx-OP-xxx` en flujos críticos y rutas de error |
| `16`/`16.xx` | Catálogo `DATA-xxx`, semántica, ownership, cobertura de persistencia y consistencia de datos intercambiados |
| `18` | Tácticas y patrones aplicados, sin redefinir contratos |
| `20` | Decisiones, excepciones y trade-offs |
| `25` | Auditoría independiente de consistencia y cumplimiento |

Una API no equivale automáticamente a un microservicio, frontend o repositorio. Define el límite por capacidad ofrecida, consumidores, owner, política de seguridad y ciclo de vida. Un contenedor puede publicar varias APIs o protocolos; una API puede ser fachada de varios contenedores. Registra un BFF por canal/capacidad solo cuando adaptación, agregación o seguridad específicas lo justifiquen.

Usa **operación** para el contrato consumible. No llames “función” a una operación salvo que documentes literalmente una implementación serverless; en ese caso conserva `API-xxx-OP-xxx` como identidad contractual y agrega el handler o función como mapeo de implementación.

## 2. Orden de generación

1. Genera `14-Vistas-C4.md`, asigna los `CT-xx` y detecta interfaces programáticas.
2. Crea el borrador de `14.00` con alcance, reglas inferidas/confirmadas, `API-xxx`, owners y consumidores.
3. Genera cada `14.xx`; asigna sus operaciones `API-xxx-OP-xxx` y contratos ejecutables sin duplicar el estándar transversal.
4. Consolida en `14.00` todas las operaciones iniciales y enlaces a contratos. Resuelve duplicados, ownership ambiguo y nombres incompatibles.
5. Cierra `14.00` antes de generar `15-Secuencias.md`; `15` referencia los IDs estables.
6. Mantén `14.00` vivo si cambia un contrato durante `16`-`24` y revalídalo en `25`.

El catálogo inicial define el contrato necesario para diseño y estimación; no inventa implementación. En preimplementación usa estados `Propuesta`, `Definida` o `Aprobada`, y deja campos desconocidos como `Missing evidence` con responsable o decisión pendiente.

## 3. Identificadores y ciclo de vida

Asigna IDs estables en el orden en que se descubren y nunca los reutilices:

- API: `API-001`, `API-002`, etc.
- Operación: `API-001-OP-001`, `API-001-OP-002`, etc.
- Error funcional reutilizable: `API-001-ERR-001`, cuando el proyecto requiera catálogo de errores.

Conserva el ID aunque cambie el nombre visible. Si una API u operación se retira, cambia su estado y conserva el registro histórico; no reasignes su consecutivo.

Estados de API u operación:

| Estado | Uso |
|---|---|
| `Propuesta` | Alcance candidato todavía no acordado |
| `Definida` | Contrato suficientemente especificado para revisión |
| `Aprobada` | Aceptada por la autoridad correspondiente |
| `Implementada` | Existe evidencia reproducible en código/configuración |
| `Deprecada` | Sigue disponible durante una transición con fecha/condición de retiro |
| `Retirada` | Ya no está disponible; conserva trazabilidad histórica |

No declares `Implementada` por intención ni `Aprobada` por decisión del agente.

## 4. Contenido obligatorio de `14.00`

### 4.1 Identificación

Incluye proyecto, versión, fecha, estado, owners, revisores, fuentes, alcance de protocolos y relación con `10.1`, `14` y `20`.

### 4.2 Decisiones de estándar

Registra la convención corporativa o baseline adoptado, versión/política, alcance y desviaciones. Una desviación material requiere `DA-xxx`, owner, motivo, riesgo y condición de revisión. No impongas una preferencia genérica cuando el proyecto ya tenga un estándar aprobado.

### 4.3 Catálogo de APIs

```markdown
| API ID | Nombre | Capacidad/dominio | Tipo | Protocolo | Owner `CT-xx`/`EXT-xx` | Consumidores | Exposición | Autenticación | Versión | Estado | Contrato/evidencia |
|---|---|---|---|---|---|---|---|---|---|---|---|
| API-001 | Nómina | Liquidación | Negocio | REST/HTTPS | CT-03 | Portal, BFF | Interna | OAuth2 | v1 | Propuesta | `14.03.1-...yaml` |
```

Clasifica el tipo como negocio/dominio, integración, experiencia/BFF, administración, eventos u otro tipo definido por la organización. Declara explícitamente si la exposición es interna, partner o pública.

### 4.4 Catálogo inicial de operaciones

Incluye las operaciones consumibles previstas u observadas; no incluyas helpers, clases ni métodos privados:

```markdown
| OP ID | API | `FAS/QA` | `operationId`/evento/RPC | Método + ruta/topic | Propósito | Consumidor | Scope/rol | Entrada | Resultado | `DATA-xxx` leído/escrito | Errores | Idempotencia | Paginación | Clasificación de datos | SLO | Owner | Estado | Contrato/evidencia |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| API-001-OP-001 | API-001 | FAS-003, QA-02 | calculatePayroll | `POST /payroll-calculations` | Iniciar cálculo | Portal | `payroll.write` | `CalculationRequest` | `202` + ID | DATA-001 | API-001-ERR-001 | Sí | N/A | Confidencial | QA-02 | Equipo Nómina | Propuesta | `14.03.1-...yaml` |
```

Para serverless agrega opcionalmente `Handler/Función` y mapea la operación a Azure Function, Lambda u otro runtime. Para eventos reemplaza método/ruta por canal/topic y declara productor, consumidores, semántica de entrega, orden, clave, esquema y compatibilidad. Para gRPC usa servicio/RPC; para GraphQL usa operación/campo y reglas de costo/profundidad cuando apliquen.

### 4.5 Matriz de trazabilidad

```markdown
| `OBJ/FAS/QA` | API | Operación | Productor/owner `CT-xx` | Consumidor | Secuencia `15` | Contrato | `DA/TP` | Prueba/evidencia |
|---|---|---|---|---|---|---|---|---|
```

Cada operación debe tener propósito, owner y consumidor identificados. Una operación sin `FAS-xxx` puede existir por operación, cumplimiento o integración, pero debe declarar el driver correspondiente.

### 4.6 Vacíos, riesgos y decisiones

Registra preguntas, inconsistencias, contratos sin owner, operaciones duplicadas, dependencias no versionadas, datos sensibles, breaking changes y decisiones pendientes. Enlaza `04`, `12`, `20` o `21` según corresponda.

## 5. Nomenclatura

Documenta una decisión explícita para cada categoría aplicable:

- nombre de API/producto y alineación con el lenguaje del dominio;
- recursos, rutas, segmentos y pluralización;
- path/query parameters, headers y `operationId`;
- campos JSON, enums, booleanos, IDs y referencias;
- fechas, horas, zonas horarias, importes, moneda, unidades y precisión;
- comandos, eventos, topics, claves de partición y versiones de esquema;
- errores funcionales y tipos de problema;
- nombres de webhooks, callbacks, servicios/RPC o campos GraphQL;
- prefijo o mecanismo de versión y política de compatibilidad.

Como reglas base, salvo estándar corporativo distinto:

- usa términos del dominio, consistentes con `22-Glosario.md`;
- usa sustantivos para recursos HTTP y reserva verbos para acciones que no modelen razonablemente un recurso;
- evita nombres tecnológicos, abreviaturas ambiguas y detalles internos en el contrato público;
- define una sola convención de casing por superficie y aplícala de forma uniforme;
- asigna `operationId` estable y único, independiente del nombre del handler;
- expresa unidades y formatos sin ambigüedad; no envíes importes monetarios sin moneda;
- no codifiques secretos, datos personales ni información mutable en rutas o nombres de topics.

No declares que una convención es “estándar” sin fuente o aprobación. Registra alternativas válidas y selecciona según ecosistema, clientes existentes y compatibilidad.

## 6. Buenas prácticas de diseño

Evalúa y documenta, cuando aplique:

- **Contrato primero:** especificar y revisar el contrato antes de acoplar consumidores a una implementación.
- **Semántica del protocolo:** métodos, estados, caché y condicionales HTTP; semántica de entrega/orden para eventos; compatibilidad de esquemas para RPC/mensajería.
- **Compatibilidad:** distinguir cambios compatibles y breaking; automatizar diff cuando exista toolchain.
- **Consistencia:** usar convenciones comunes para paginación, filtros, ordenamiento, búsquedas, expansión y campos parciales.
- **Errores:** estructura uniforme, código funcional estable, mensaje seguro, correlación y detalle accionable; para HTTP considerar Problem Details según el baseline aprobado.
- **Idempotencia y concurrencia:** definir claves, ventana, persistencia del resultado y comportamiento ante duplicados; usar control optimista/condicional cuando corresponda.
- **Operaciones largas:** preferir aceptación asíncrona, recurso de estado, callback o evento cuando no sea viable responder sincrónicamente.
- **Volumen:** declarar límites de payload, páginas, lotes, profundidad, complejidad y tiempos máximos.
- **Evolución:** evitar versionar por cada cambio; versionar o crear compatibilidad cuando el contrato observable se rompa.
- **Ejemplos y pruebas:** incluir ejemplos válidos/de error y casos de contrato trazados a operaciones críticas.
- **Cobertura de persistencia:** toda operación que cree, modifique, lea o elimine estado material declara los `DATA-xxx` afectados; sus schemas se mapean en la matriz de cobertura del `16.xx` dueño.
- **Streaming/push:** para SSE, WebSocket, streaming HTTP, callbacks o canales conversacionales define protocolo concreto, tipos discriminados de mensaje/evento, orden, correlación, finalización, heartbeat cuando aplique, errores, backpressure/límites, idempotencia, reconexión y reanudación. La palabra “streaming” sin contrato de frames/eventos no alcanza estado `Definida`.

### 6.1 Protocolos agente↔UI y UI generativa

Cuando una API conecte frontend y agente, distingue tres cosas que suelen confundirse:

- **librería/kit de UI** (assistant-ui, Vercel AI SDK UI, OpenAI ChatKit, CopilotKit u otro):
  implementación cliente/runtime; no es por sí misma el contrato entre desplegables;
- **protocolo agente↔UI** (por ejemplo AG-UI o uno propio): envelope, eventos, estado,
  correlación, interrupts, transporte, errores y reanudación;
- **especificación de UI generativa** (por ejemplo A2UI): surfaces/componentes declarativos,
  catálogo, data binding, acciones y validación; puede viajar sobre el protocolo anterior u otro
  transporte, por lo que no lo reemplaza automáticamente.

Si se adopta AG-UI, A2UI u otro estándar, registra versión/baseline, fuente oficial y fecha;
define el mapping entre sus eventos/mensajes y los `API-xxx-OP-xxx`, schemas y estados internos.
Si se conserva un contrato propio, documenta el mapping equivalente y la razón de no adoptar el
estándar. No etiquetes una operación como “AG-UI”, “A2UI” o “compatible” sin contrato y prueba de
compatibilidad verificables.

Para agent↔UI cubre como mínimo, según aplique: run/thread/message IDs, inicio/progreso/cierre,
text deltas, tool call/proposal/result, confirmación/rechazo/interrupt-resume, snapshots/deltas de
estado, cancelación, errores, orden, deduplicación, idempotencia y reconexión/reanudación. Para UI
generativa añade surface/catalog ID, versión de schema, componentes/props permitidos, data model,
acciones y respuestas, validación, límites, payload inválido y fallback.

No conviertas `14.00` en un manual genérico: conserva únicamente reglas adoptadas, decisiones del proyecto, catálogo y evidencia. Enlaza la guía corporativa cuando exista.

## 7. Seguridad, resiliencia y operación

Para cada API/operación determina y registra:

- autenticación, autorización por función/objeto/propiedad y scopes/roles;
- exposición, frontera de confianza, clasificación/minimización de datos y masking;
- validación de entrada, asignación explícita de campos y límites contra abuso;
- para agentic/generative UI, allowlist de componentes y acciones, validación de schemas/data
  binding, autorización server-side de toda acción, tratamiento de instrucciones/datos no
  confiables y prohibición de ejecutar código arbitrario enviado por el agente;
- TLS, CORS, protección de webhooks/callbacks, secretos y allowlists cuando apliquen;
- rate limit, cuota, throttling y respuesta ante agotamiento;
- timeout total y por salto, política de retry con backoff/jitter e idempotencia;
- circuit breaker, bulkhead, fallback y degradación cuando estén justificados por `QA-xx`;
- `traceparent` o estándar de trazabilidad aprobado, correlation ID, logs seguros y métricas;
- SLI/SLO, alertas, auditoría, runbook, owner y soporte;
- amenazas relevantes del OWASP API Security Top 10 o modelo de amenazas adoptado.

Cuando `19.1` aplique, cada API/operación enlaza los `THR-xxx`/`SEC-xxx` que condicionan su
diseño y su criterio de aceptación. `14.00`/`14.xx` poseen los controles de aplicación y
contrato; Vulcano operacionaliza scanners, pruebas/gates, evidencia continua y remediación sin
renumerar ni redefinir los `SEC-xxx`.

No apliques Retry, Circuit Breaker, API Gateway, BFF o caché por defecto. Enlaza el `TP-xxx` de `18` y demuestra el fallo/driver que resuelve, parámetros, trade-offs y validación.

## 8. Contratos ejecutables

El Markdown es catálogo y gobierno; no sustituye el contrato procesable. Genera el formato que corresponda al protocolo y baseline:

- OpenAPI para REST/HTTP;
- AsyncAPI para eventos/mensajería cuando aplique al ecosistema;
- `.proto` para gRPC/Protocol Buffers;
- schema SDL para GraphQL;
- JSON Schema u otro esquema aprobado para payloads compartidos.

Nombra cada asset bajo el `14.xx` del contenedor owner, con consecutivo estable:

- `14.03.1-OpenAPI_API-001_Nomina.yaml`
- `14.03.2-AsyncAPI_API-002_Eventos-Nomina.yaml`
- `14.04.1-Proto_API-003_Consulta-Empleados.proto`
- `14.05.1-GraphQL_API-004_Portal.graphql`

Cada contrato debe:

- declarar título/nombre, versión, owner/contacto y ambientes/servidores sin secretos;
- usar los mismos `API-xxx` y `API-xxx-OP-xxx` mediante descripción, extensión o tabla de mapeo;
- definir seguridad, entradas, salidas, errores y ejemplos aplicables;
- resolver referencias y pasar el linter/validador adoptado;
- evitar contradicciones con `14.00`, `14.xx`, `15`, `16.xx` y `20`.
- declarar o mapear los `DATA-xxx` leídos/escritos por sus operaciones cuando exista persistencia, sin filtrar nombres físicos internos al contrato público si no son necesarios;
- para tiempo real/streaming, definir los schemas de cada evento/frame y la máquina observable de inicio, progreso, confirmación, finalización y error.
- para protocolos agent↔UI o UI generativa, declarar versión/baseline y mapping; validar envelopes,
  eventos, surfaces/componentes/acciones y fallbacks con JSON Schema, AsyncAPI u otro contrato
  procesable adecuado. El schema estándar referenciado no sustituye extensiones propias ni su
  compatibilidad documentada.

Para una API de tercero usa `EXT-xx` como owner, enlaza su especificación autoritativa y cataloga solo las operaciones realmente consumidas. No inventes ni declares canónico un contrato externo ausente. Si necesitas conservar un snapshot para desarrollo o auditoría, ubícalo bajo el `14.xx` consumidor, márcalo `Copia no canónica`, registra fuente/fecha/versión y define cómo detectar cambios del proveedor.

Si aún no procede crear un contrato completo, registra `Contrato pendiente`, owner y condición de elaboración; deja `14.00` en `No cumple` cuando el contrato sea necesario para una operación crítica o un consumidor externo.

## 8.1 Mapeo profundo de integraciones externas

Cuando el usuario comparte documentación real de un `EXT-xx` (documento compartido, colección Postman o una
URL alcanzable) con detalle suficiente para mapear campos — no solo para catalogar la operación — genera
`14.xx.N-Mapeo-Integracion_EXT-xx_<Sistema>.md` siguiendo `references/guia-mapeo-integraciones-externas.md`.
`N` continúa el consecutivo del `14.xx` dueño del adaptador/ACL, después de sus contratos ejecutables
propios. Este artefacto profundiza una integración ya catalogada en `14.00`; no crea IDs de operación
paralelos ni un registro de gaps propio — los vacíos se registran en `12`/`21` como cualquier otro.

## 9. Aplicación por escenario

### Caso A — Greenfield

Genera catálogo y contratos como diseño objetivo. Distingue `Propuesta`, `Definida` y `Aprobada`; no inventes URLs productivas, credenciales, owners personales, SLO ni evidencia de implementación.

### Caso B — AS-IS

Deriva APIs y operaciones desde especificaciones existentes, rutas/controllers, gateways, schemas, topics, clientes, configuración y pruebas. Cita archivo/línea, hash o evidencia equivalente. Marca diferencias entre contrato publicado y comportamiento observado; una interfaz sin documentación es un hallazgo, no una licencia para completar datos por inferencia silenciosa.

### Caso C — TO-BE

Conserva la correspondencia `AS-IS → TO-BE`: API/operación actual, destino, compatibilidad, coexistencia, consumidores, migración, deprecación, fecha/condición de retiro y rollback. Enlaza brechas `23` y fases `24`.

## 10. Criterios de cierre

No cierres `14.00` hasta que:

- el alcance y los protocolos aplicables estén declarados;
- cada API y operación tenga ID estable, propósito, owner `CT-xx`/`EXT-xx`, consumidor, exposición, seguridad, estado y enlace al contrato/evidencia;
- las reglas de nomenclatura y compatibilidad sean explícitas y no contradigan el estándar organizacional;
- cada operación esté trazada a `CT-xx` y a `FAS/QA` o a otro driver documentado;
- las operaciones críticas definan errores, idempotencia/concurrencia, datos, límites y SLO aplicables;
- cada contrato ejecutable requerido exista, valide y coincida con el catálogo;
- cada operación con persistencia enlace `DATA-xxx` y coincida con la matriz del `16.xx` dueño;
- ninguna operación que soporte una `FAS-xxx` o `QA-xx` priorizada permanezca `Propuesta`; debe ser al menos `Definida`, o el gate queda abierto con incertidumbre, owner y fecha en `12`;
- todo contrato streaming/push defina protocolo y schemas observables, además de correlación, cierre, error y reconexión/reanudación aplicable;
- todo protocolo agent↔UI o UI generativa declare versión/baseline, mapping a operaciones y
  estados internos, catálogo/acciones permitidos, validación, seguridad y fallback aplicables;
- no existan APIs duplicadas, contratos sin owner ni breaking changes sin disposición;
- las desviaciones enlacen `DA-xxx` y los riesgos/vacíos enlacen su documento dueño;
- Caso B aporte evidencia reproducible y Caso C documente compatibilidad y transición;
- `15` pueda referenciar IDs estables sin redefinir las operaciones.

Trata como bloqueante en `25` una API crítica sin owner/consumidor, una operación crítica sin contrato verificable, una contradicción entre catálogo y contrato, una autorización indefinida para datos sensibles o un breaking change sin plan de coexistencia/migración.

Si después de cerrar `14.00` cambia una `FAS`, un `DATA-xxx`, una operación o un schema, reabre `14.00`, el `14.xx` owner, el contrato ejecutable, las secuencias y el modelo `16.xx`; invalida los hashes de `25` y repite los checkpoints según la sección “Reapertura incremental por cambios” de `SKILL.md`.

Referencias normativas recomendadas: especificación OpenAPI vigente aprobada por la organización, RFC 9110 para semántica HTTP, RFC 9457 para Problem Details, W3C Trace Context y OWASP API Security Top 10. Registra en `14.00` las versiones/baselines realmente adoptados; no asumas automáticamente la versión más reciente.
