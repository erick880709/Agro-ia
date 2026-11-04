# Guía: Diseño detallado por contenedor significativo

Aplica en los Casos A, B y C cuando se generan `14-Vistas-C4.md` y `16-Modelo-de-Datos.md`. El objetivo es profundizar donde existe riesgo o complejidad sin crear documentación vacía para cada proceso, base administrada o servicio trivial.

## Contenido

1. [Inventariar y clasificar contenedores](#1-inventariar-y-clasificar-contenedores)
2. [Numeración estable](#2-numeración-estable)
3. [Contenido de cada `14.xx`](#3-contenido-de-cada-14xx)
4. [Contenido de cada `16.xx`](#4-contenido-de-cada-16xx)
   - [Identidad y catálogo de datos](#41-identidad-y-catálogo-de-datos)
   - [Nivel de madurez](#42-nivel-de-madurez)
   - [Matriz de cobertura de persistencia](#43-matriz-de-cobertura-de-persistencia)
   - [Esquema físico y validación](#44-esquema-físico-y-validación)
   - [Diccionario físico exhaustivo](#45-diccionario-físico-exhaustivo)
5. [Gate de completitud](#5-gate-de-completitud)

## 1. Inventariar y clasificar contenedores

Parte del C4 Nivel 2 y asigna a cada contenedor dentro del límite del sistema un ID estable `CT-01`, `CT-02`, etc.; muestra el ID en el diagrama y en las tablas. Asigna los IDs en el orden de declaración del código Mermaid del Nivel 2. En revisiones posteriores conserva los existentes y agrega nuevos contenedores al final: nunca renumeres. Los sistemas externos usan `EXT-xx` y no reciben `14.xx`. Un contenedor es **significativo** cuando cumple al menos uno de estos criterios:

- implementa una o más `FAS-xxx`;
- soporta un `QA-xx` prioritario o concentra una táctica crítica;
- contiene lógica de dominio, workflow o estado complejo;
- posee datos o es fuente de verdad de información relevante;
- cruza una frontera de seguridad, confianza o cumplimiento;
- integra terceros o usa comunicación asíncrona relevante;
- requiere despliegue, escalamiento u operación independiente;
- contiene una incertidumbre de `12` o fue objeto de una PoC de `13`;
- en AS-IS, concentra deuda, acoplamiento o riesgo verificable.

Un frontend web, móvil o administrativo puede ser significativo igual que un microservicio. Una base administrada, cola, proxy o servicio CRUD simple no lo es automáticamente: documenta la razón si se clasifica como no significativo. Atribuye el modelo de datos al contenedor lógico que es dueño de la información (por ejemplo, el servicio de Nómina), no al contenedor técnico PostgreSQL que la almacena.

Para Microfrontends sigue `references/guia-microfrontends.md`: asigna `CT-xx` al shell o a una unidad UI solo si tiene build, versión, despliegue y boundary runtime independientes con owner claro. Un feature module, paquete o librería compilado y desplegado junto con el portal es un componente interno de su `14.xx`, aunque el equipo lo denomine microfrontend. No generes correspondencia automática microservicio → microfrontend.

Incluye en `14-Vistas-C4.md` esta matriz de cobertura. Una fila puede cubrir varias capacidades agrupadas en el mismo desplegable y una capacidad puede requerir varios contenedores; conserva el enlace explícito con la configuración aprobada en `10`:

```markdown
| ID | Contenedor | Capacidad/scope de `10` | Tipo | ¿Significativo? | Motivo (`QA/FAS/riesgo`) | Diseño C4 | Modelo de datos/estado |
|---|---|---|---|---|---|---|---|
| CT-01 | Portal Web | Gestión de empleados / FAS-001 | Frontend | Sí | FAS-001, QA-03 | `14.01-...` | `16.01-...` / No aplica |
| CT-02 | Shell RR. HH. | Composición de experiencia / QA-04 | Frontend shell | Sí | Routing, identidad y carga de remotes | `14.02-...` | No aplica — solo sesión remota |
```

## 2. Numeración estable

Usa el mismo sufijo decimal, con un mínimo de dos dígitos, para el mismo contenedor. Después de `CT-99` continúa con `CT-100`/`14.100`/`16.100` sin renumerar:

- `14-Vistas-C4.md`: índice, C4 Nivel 2 y matriz de cobertura.
- `14.00-Gobierno-y-Catalogo-Inicial-de-APIs_<Proyecto>.md`: gobierno transversal; el sufijo `00` está reservado y no representa un contenedor.
- `14.01-Diseno-Detallado_CT-01_<Contenedor>.md`: C4 Nivel 3 del `CT-01`.
- `16-Modelo-de-Datos.md`: panorama, propiedad y relaciones de datos entre contenedores.
- `16.01-Modelo-de-Datos_CT-01_<Contenedor>.md`: datos o estado del `CT-01`.

Reserva el sufijo aunque un contenedor no necesite archivo de datos. Por ejemplo, `CT-02` puede tener `14.02` y no tener `16.02`; la matriz registra `No aplica` y la razón. Nunca reasignes un sufijo a otro contenedor en una revisión posterior.

Los contratos ejecutables heredan el prefijo del `14.xx` owner y un consecutivo estable, por ejemplo `14.01.1-OpenAPI_API-001_Empleados.yaml`. La subnumeración `17.1`-`17.5` no sigue este esquema: son cinco tipos fijos de artefactos de despliegue y costos, no IDs de contenedor.

Los esquemas físicos procesables heredan el prefijo del `16.xx` owner y un consecutivo estable, por ejemplo `16.03.1-Schema_DATA-004_Nomina.sql` o `16.03.2-Modelo_DATA-005_Conceptos.dbml`. El formato depende del baseline real (`.sql`, DBML, Prisma, Liquibase/Flyway, esquema ORM u otro), pero debe ser procesable por una herramienta y no una segunda descripción narrativa.

## 3. Contenido de cada `14.xx`

Genera un archivo por cada contenedor significativo con:

1. ID, nombre, capacidades/scopes asignados en `10`, tipo, tecnología/baseline de `10.1`, equipo/owner y motivo de significancia.
2. Responsabilidad, alcance, límites y capacidades que implementa.
3. C4 Nivel 3 propio, abriendo únicamente ese contenedor.
4. Tabla de componentes internos: responsabilidad, interfaces, dependencias, `QA-xx`/`FAS-xxx` satisfechos y patrones significativos. Declara la organización interna del contenedor — por ejemplo Hexagonal o Capas — y los patrones de diseño locales; para cada patrón indica problema, alcance, alternativa simple descartada y evidencia/criterio de validación. No impongas Hexagonal por criticidad solamente: exige dominio relevante o dependencias variables que realmente deban aislarse. No agregues patrones por decoración. Cuando un componente sea de visualización de datos, dashboard, analítica o reportería, nombra la librería/motor de gráficos concreto (o `Por decidir` con owner y fecha) en vez de describir solo la necesidad; esa tecnología debe coincidir con el baseline de `10.1` o actualizarlo.
5. Contratos de entrada/salida, APIs, eventos, jobs e integraciones. Si existen interfaces programáticas, sigue `references/guia-gobierno-y-diseno-apis.md`: referencia los `API-xxx`/`API-xxx-OP-xxx` que publica o consume, aplica las reglas de `14.00`, enlaza los flujos de `15`, genera/enlaza el contrato ejecutable propiedad de este `CT-xx` y, para terceros, enlaza la fuente autoritativa o snapshot no canónico sin copiar esquemas completos al Markdown. Cuando el contrato incluya comunicación en tiempo real (WebSocket, SSE, streaming u otro push), no lo etiquetes solo como "REST + WS": especifica protocolo/librería concreta en cliente y servidor, mecanismo que transporta el evento de dominio hasta la conexión abierta (pub/sub, cola, canal in-process) y política de reconexión/fallback; si algo queda pendiente, dilo explícitamente con owner y fecha en vez de omitirlo.
6. Tácticas y patrones aplicados dentro del contenedor; enlaza los `TP-xxx` de `18`, las dimensiones de `19` y las `DA-xxx` de `20`. Clasifica cada elemento según `references/guia-catalogo-patrones.md` como táctica arquitectónica, patrón arquitectónico, patrón de diseño, patrón cloud o patrón IA. `14.xx` explica su aplicación interna, pero no duplica la ficha ni el diagrama mecánico cuyo dueño sea `18`.
7. Dependencias y puntos de acoplamiento permitidos/prohibidos.
8. Modelo de datos/estado: enlaza el `16.xx` correspondiente o justifica `No aplica`. Evalúa CQRS por bounded context, contenedor o caso de uso; si aplica, separa comandos, modelo de escritura, proyecciones/lecturas, ownership, lag, consistencia, reconstrucción y operación. Si un único modelo basta, registra el descarte sin forzar CQRS.
9. Riesgos, incertidumbres resueltas/abiertas y decisiones pendientes.
10. Diseño de código y Clean Code según `references/guia-clean-code.md`: identifica las reglas `CC-xxx` aplicables, cómo se implementan en el contenedor, automatización prevista o existente, umbral o condición de aceptación, evidencia y excepciones con responsable. En Casos A/C una regla puede quedar `Definida` hasta contar con código; en Caso B no la marques `Aplicada` o `Validada` sin evidencia del repositorio.

Si el `CT-xx` es shell o microfrontend, agrega el detalle exigido por `references/guia-microfrontends.md`: rutas y contratos públicos, mecanismo de composición/versionado, estado permitido/prohibido, design system/accesibilidad/i18n, autenticación/autorización, dependencias compartidas, presupuesto de carga, aislamiento/fallback, telemetría, capacidad de entrega independiente, compatibilidad y rollback; enlaza pipeline AS-IS/Vulcano cuando exista. Documenta imports directos, store global o eventos sin esquema como acoplamientos/riesgos, no como integración aceptada por omisión.

Si el `CT-xx` implementa una interfaz conversacional o agentic UI, agrega una subsección
`## Realización de Agent UX` con:

```markdown
| Iris (`SURF/SCR/CMP/ST/ERR/TC`) | Componente concreto | UI kit | Runtime/estado | Protocolo/eventos | Adapter/owner | Contrato/API-OP | Evidencia/prueba |
|---|---|---|---|---|---|---|---|
```

Explica composer/messages, tool rendering, proposed action, confirmación/rechazo, cancelación,
threads/historial, loading/progress/error/completed, accesibilidad y fallback. Distingue las capas
del baseline de `10.1`; assistant-ui, Vercel AI SDK UI, AG-UI, A2UI, OpenAI ChatKit o CopilotKit
solo aparecen si fueron observados/seleccionados o permanecen explícitamente `Por decidir` con
owner. El `14.xx` mapea la realización; no redefine los contratos UX de Iris.

Para AG-UI, A2UI u otro estándar/protocolo seleccionado, declara versión/baseline y mapping entre
eventos/surfaces externos y el modelo interno. Para UI generativa incluye catálogo allowlisted,
propiedades/data binding admitidos, acciones autorizadas, validación, tratamiento de payload
inválido y fallback accesible; nunca ejecutar código arbitrario recibido del agente.

Incluye C4 Nivel 4 o diagrama de paquetes solo cuando una parte crítica requiera detalle de código. No conviertas `14.xx` en especificación de clases, endpoints o métodos triviales: el inventario inicial de operaciones vive en `14.00` y el detalle procesable en OpenAPI, AsyncAPI, `.proto`, GraphQL SDL u otro contrato aprobado.

## 4. Contenido de cada `16.xx`

Genera `16.xx` para cada contenedor significativo que posea datos persistentes o estado no trivial. En frontends aplica cuando exista estado persistido/offline, caché funcional, sincronización o un modelo de estado complejo; si solo representa datos remotos, documenta `No aplica`.

Incluye:

1. tipo(s) de motor de datos elegido (relacional, documental, clave-valor, columnar, grafo, series de tiempo, búsqueda, etc.) y justificación siguiendo `references/guia-catalogo-bases-de-datos.md`; si hay 2 o más motores real y actualmente viables sin trade-off obvio, enlaza la matriz de `references/guia-matriz-decision.md`;
2. responsabilidad y propiedad de los datos; fuente de verdad;
3. modelo conceptual/lógico y diagrama ER cuando existan relaciones no triviales;
4. agregados, entidades, value objects o estructuras principales;
5. claves, restricciones, índices, particionamiento y estrategia de consultas;
6. consistencia, límites transaccionales, concurrencia e idempotencia;
7. contratos/eventos de datos y duplicación controlada entre contenedores;
8. migraciones, compatibilidad y versionado;
9. clasificación de datos, PII, cifrado, retención, auditoría y borrado;
10. backup, recuperación, archivado y supuestos de volumen.

### 4.1 Identidad y catálogo de datos

Asigna un ID estable `DATA-xxx` a cada conjunto persistente o estado material con ciclo de vida, ownership o política propia: agregado transaccional, historial, proyección, índice, caché funcional, archivo o dataset analítico. El catálogo canónico vive en `16-Modelo-de-Datos.md`; el detalle y las referencias viven en el `16.xx` dueño. No asignes un ID por columna ni por DTO.

El catálogo global incluye como mínimo:

```markdown
| DATA ID | Nombre | Owner `CT-xx` | Fuente de verdad | Motor/store | Sensibilidad | Retención/borrado | Modelo dueño | Estado |
|---|---|---|---|---|---|---|---|---|
```

### 4.2 Nivel de madurez

Cada `16.xx` declara explícitamente:

```markdown
## Nivel de madurez del modelo
**Objetivo de entrega:** [Arquitectónico/Listo para implementación/Observado AS-IS]

| Nivel | Estado | Evidencia | Vacío/condición para avanzar | Owner |
|---|---|---|---|---|
| Conceptual | [Completo/No aplica] | ... | ... | ... |
| Lógico | [Completo/Parcial/No aplica] | ... | ... | ... |
| Físico | [Completo/Parcial/No requerido todavía] | ... | ... | ... |
```

- **Arquitectónico:** exige niveles conceptual y lógico suficientes para resolver ownership, relaciones, invariantes, consultas, seguridad y operación. El físico puede quedar `No requerido todavía` únicamente con trigger, owner y momento de elaboración.
- **Listo para implementación:** exige nivel físico completo y un asset procesable `16.xx.y` con tablas/colecciones, campos y tipos, PK/FK o equivalentes, nulabilidad, restricciones, índices, particiones aplicables y mecanismo de migración/versionado. Un ER o una lista de entidades no sustituye este asset.
- **Observado AS-IS:** enlaza DDL, migraciones, ORM o esquema real. Si no existe evidencia, registra la limitación/hallazgo; no reconstruyas silenciosamente un físico supuesto.

El objetivo `Listo para implementación` también se activa cuando el usuario pide modelo físico/DDL, cuando el esquema es insumo necesario de estimación o migración, o cuando el artefacto se presenta como listo para construir.

### 4.3 Matriz de cobertura de persistencia

Cada `16.xx` contiene una fila por escritura, lectura material o estado persistido relevante:

```markdown
## Matriz de cobertura de persistencia
| Driver `FAS/QA/SEC/otro` | API/OP/evento/job/origen | Esquema de intercambio | `DATA-xxx` | Entidad/estructura lógica | Tabla/colección/objeto/store | Operación y consulta dominante | Clasificación | Retención/borrado |
|---|---|---|---|---|---|---|---|---|
```

Usa `N/A — <motivo>` cuando el dato no cruce una interfaz programática. Toda afirmación en `14.xx`, `15`, `18`, `19.1` o un contrato de que algo se “persiste”, “guarda”, “registra”, “mantiene historial” o actúa como fuente de verdad debe resolver a una fila y a un `DATA-xxx`. La matriz no reemplaza el modelo: demuestra su cobertura.

En sistemas con LLM, diferencia contenido visible/auditable, invocaciones de herramientas y metadatos operativos del razonamiento interno del modelo. No diseñes persistencia de chain-of-thought; conserva únicamente mensajes necesarios, decisiones observables, evidencia, resúmenes seguros y referencias a adjuntos según retención/minimización.

### 4.4 Esquema físico y validación

Cuando el nivel físico sea requerido:

- enlaza el asset `16.xx.y` desde el `16.xx` y desde la fila `DATA-xxx` aplicable;
- declara dialecto/formato y versión;
- valida sintaxis y referencias con el motor, parser o linter adoptado y registra comando/resultado; si la herramienta todavía no está disponible, el nivel permanece `Parcial` y el artefacto en `No cumple`;
- alinea nombres y tipos con los esquemas de OpenAPI/AsyncAPI/Proto/GraphQL sin acoplar el contrato público a nombres internos innecesarios;
- documenta la primera migración, compatibilidad hacia atrás, rollback y tratamiento de datos existentes;
- evita guardar secretos, credenciales o razonamiento privado del modelo en ejemplos o fixtures.

### 4.5 Diccionario físico exhaustivo

Cuando exista un asset físico `16.xx.y`, agrega al `16.xx` dueño la sección exacta `## Diccionario físico de datos` siguiendo `references/guia-diccionario-fisico-datos.md`.

La cobertura es 1:1 y obligatoria: cada tabla, colección, vista, proyección u objeto equivalente del asset tiene una subsección; cada campo/columna física tiene una fila. Documenta propósito, `DATA-xxx`, owner, rol del dato, clasificación, retención/borrado, seguridad/RLS, consumidores y, por campo, tipo, nulabilidad, default, clave/referencia, restricciones, PII y descripción. No basta con mencionar nombres agrupados en la matriz de persistencia ni con enlazar el DDL.

Valida las dos direcciones: objeto/campo físico sin documentación y entrada documentada sin objeto/campo físico. Para SQL ejecuta `validate_architecture_coherence.py`; para otro formato usa el parser o inventario nativo y registra comando/resultado. Toda diferencia deja la madurez física en `Parcial` y el `16.xx` en `No cumple`.

`16-Modelo-de-Datos.md` no repite estos detalles: mantiene el mapa de ownership, flujos entre contenedores y enlaces a todos los `16.xx`.

## 5. Gate de completitud

No cierres `14`-`16` hasta que:

- todos los contenedores del Nivel 2 estén clasificados;
- todas las capacidades incluidas en la configuración de `10` estén mapeadas a uno o más `CT-xx`, sin separaciones o agrupaciones no aprobadas;
- cada contenedor significativo tenga su `14.xx`;
- cuando existan interfaces programáticas, `14.00` esté consolidado, cada `API-xxx`/`API-xxx-OP-xxx` tenga owner/consumidor/estado/contrato o evidencia, y cada `14.xx` coincida con el catálogo y posea sus contratos ejecutables;
- cada contenedor significativo con estado relevante tenga su `16.xx`;
- `16` catalogue cada conjunto persistente relevante como `DATA-xxx`, sin IDs duplicados ni ownership ambiguo;
- cada `16.xx` declare objetivo de entrega, madurez conceptual/lógica/física y matriz de cobertura de persistencia; toda persistencia narrada en otro artefacto resuelva a una fila, un `DATA-xxx` y un modelo;
- todo modelo `Listo para implementación` tenga un esquema físico procesable `16.xx.y`, validación registrada, estrategia de migración/rollback y diccionario físico exhaustivo con correspondencia 1:1 de objetos/campos; un DDL sin documentación semántica o un modelo meramente conceptual no cierre ese objetivo;
- cada omisión tenga una justificación explícita en la matriz;
- cada contenedor significativo con código propio documente organización interna y patrones relevantes o justifique que no requiere uno, evalúe CQRS solo en su scope y aplique las reglas `CC-xxx` pertinentes sin inventar métricas ni evidencia;
- todo componente de visualización/dashboard/analítica/reportería nombre su librería de gráficos y todo contrato en tiempo real nombre su protocolo/mecanismo concreto (transporte cliente-servidor y puente evento-de-dominio → conexión), sin dejarlo implícito ni genérico;
- todo frontend conversacional/agentic UI tenga mapping
  `SURF/SCR/CMP/ST/ERR/TC → componente/runtime/protocolo/adapter → API-OP/contrato → prueba`, y
  las capas coincidan con `10.1`; si existe UI generativa, catálogo, validación, autorización y
  fallback quedan explícitos;
- ninguna `API-xxx-OP-xxx` que soporte una `FAS-xxx`/`QA-xx` priorizada cierre este gate en estado `Propuesta`: debe alcanzar al menos `Definida` antes de cerrar `14`-`16`, o quedar `Por decidir` con owner y fecha registrados como incertidumbre abierta en `12`;
- cada operación que lea/escriba datos persistentes enlace el `DATA-xxx` y el esquema de intercambio correspondiente; diferencias entre contrato y modelo tengan mapeo o decisión explícita;
- tecnologías, runtimes, stores, servicios y hosting coincidan con `10.1`; toda desviación actualice el arquetipo y enlace una decisión/evidencia;
- cuando aplique Microfrontends, `09`/`10` demuestren driver y selección frente a SPA modular; `10.1` registre el subarquetipo; cada unidad realmente independiente tenga `CT-xx`, `14.xx`, owner y capacidad de despliegue/rollback autónoma; el pipeline detallado vive en Vulcano o se cita como evidencia AS-IS; y los módulos publicados juntos permanezcan como componentes;
- los IDs, nombres, contratos y ownership coincidan entre `14`, `14.00`, `14.xx`, `15`, `16`, `17` y `20`.

En Caso B, cada detalle y relación debe apuntar a evidencia del repositorio. En Caso C, indica en cada `14.xx`/`16.xx` qué se conserva, cambia o elimina respecto al AS-IS. La revisión `25` trata cualquier incumplimiento de este gate como hallazgo bloqueante.
