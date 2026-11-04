# Guía: Catálogo y selección de motores de base de datos

Complementa `references/cuestionario-linea-base.md`, `references/guia-diseno-detallado-contenedores.md`, `references/guia-matriz-decision.md` y `16-Modelo-de-Datos.md`/`16.xx`. Es un catálogo de candidatos, no una lista cerrada ni de compra: usa un tipo de motor solo cuando el patrón de acceso real del contenedor lo exige, y conserva evidencia de la comparación.

## Contenido

1. Taxonomía de tipos de motor
2. Criterios de selección
3. Consistencia: CAP y PACELC
4. Catálogo por tipo
5. Persistencia poliglota
6. Validación mínima
7. Enrutamiento documental
8. Validación experta con `dba`

## 1. Taxonomía de tipos de motor

| Tipo | Modelo de datos | Motores de referencia |
|---|---|---|
| Relacional (SQL) | Filas/tablas con esquema fijo e integridad referencial | PostgreSQL, MySQL, SQL Server, Oracle |
| Documental | Documentos semi-estructurados con esquema flexible por documento | MongoDB, Firestore, Cosmos DB (API documento) |
| Clave-valor | Par clave → valor opaco, sin joins | DynamoDB, Redis (modo persistente), Riak |
| Columnar ancha | Familias de columnas dispersas por fila, optimizada a escritura | Cassandra, HBase, Bigtable |
| Grafo | Nodos/aristas con el recorrido de relaciones como ciudadano de primera clase | Neo4j, Amazon Neptune, ArangoDB |
| Series de tiempo | Puntos con timestamp, escritura secuencial y agregación por ventana | TimescaleDB, InfluxDB, Amazon Timestream |
| Motor de búsqueda | Índice invertido con ranking y relevancia | Elasticsearch, OpenSearch, Algolia |
| Cache in-memory | Estructuras en memoria con TTL | Redis, Memcached |
| Data warehouse analítico | Columnar OLAP de alta compresión para consultas agregadas masivas | Snowflake, BigQuery, Redshift |
| Data lake / object storage | Archivos crudos o semi-estructurados a gran escala, esquema en lectura | S3 + Parquet/Iceberg, ADLS Gen2, GCS |

Clasifica por el patrón de acceso dominante del contenedor, no por popularidad ni por lo que ya usa otro proyecto. Un mismo bounded context puede necesitar más de un tipo — ver sección 5.

## 2. Criterios de selección

| Dimensión | Pregunta que decide |
|---|---|
| Patrón de acceso | ¿Lecturas por clave, consultas ad hoc con joins, texto libre, rango de tiempo o recorrido de relaciones? |
| Forma del esquema | ¿Fijo y estable entre entidades, o cambia por entidad / itera con frecuencia? |
| Consistencia requerida | ¿Exige ACID fuerte o tolera consistencia eventual? (sección 3) |
| Escala de lectura/escritura | ¿Un solo nodo basta o se necesita partición horizontal desde el día uno? |
| Transaccionalidad | ¿Hay invariantes multi-entidad dentro de una transacción, o los agregados ya están acotados a un límite transaccional? |
| Volumen y retención | ¿Crecimiento proyectado, política de retención/archivado/downsampling? |
| Latencia objetivo | ¿Milisegundos de punta a punta, o tolera consultas más lentas por ser analítico? |
| Ecosistema y operación | ¿El equipo ya opera el motor, existe servicio administrado en el proveedor elegido, hay licenciamiento o lock-in relevante? |

Reutiliza `QA-xx` de `05-Atributos-de-Calidad.md` para priorizar estas dimensiones; no las inventes sueltas.

## 3. Consistencia: CAP y PACELC

Bajo una partición de red, un motor distribuido elige **Consistencia** o **Disponibilidad** (teorema CAP); en operación normal, sin partición, PACELC agrega el trade-off **Latencia vs. Consistencia** que cada motor resuelve incluso sin fallos.

No lo cites como argumento de venta: documenta qué elige el motor candidato y si el dominio tolera ese trade-off. Un módulo de inventario o de nómina normalmente no tolera lecturas obsoletas (prioriza consistencia); un feed de actividad o un contador de vistas normalmente sí (prioriza disponibilidad/latencia). La elección correcta depende del bounded context, no del motor "más moderno".

## 4. Catálogo por tipo

| Tipo | Úsalo cuando | Evítalo cuando | Debe validar |
|---|---|---|---|
| Relacional (SQL) | Hay relaciones estables, invariantes fuertes multi-entidad y consultas ad hoc con joins | El esquema cambia por entidad o la escala de escritura excede un solo nodo/clúster gestionable | Integridad referencial, aislamiento de transacciones, plan de escalado (réplicas de lectura, partición) |
| Documental | El agregado se lee/escribe completo y su forma varía entre instancias o itera rápido | Se necesitan joins transversales frecuentes entre colecciones o invariantes multi-documento fuertes | Límite del agregado, versionado de esquema, consultas que cruzan colecciones |
| Clave-valor | Acceso por clave predecible a muy baja latencia y alto throughput (sesión, carrito, feature flag) | Se necesitan consultas por atributos secundarios o relaciones entre claves | Diseño de la clave, hot partitions, expiración/TTL |
| Columnar ancha | Escritura masiva distribuida con partición por clave y tolerancia a partición sobre consistencia fuerte | El caso exige transacciones multi-fila o consultas ad hoc no anticipadas en el diseño de la clave | Estrategia de partición/rebalanceo, consultas soportadas vs. no soportadas, reparación/compactación |
| Grafo | Las consultas de relación profunda o variable (recomendación, fraude, jerarquías) degradan con joins SQL múltiples | El dominio es mayormente tabular sin recorridos de relación relevantes | Profundidad de recorrido esperada, modelo de nodos/aristas, rendimiento con el volumen real |
| Series de tiempo | Métricas, IoT u observabilidad con escritura secuencial y agregación por ventana/retención por antigüedad | Los datos no tienen componente temporal dominante en el acceso | Cardinalidad de series, política de retención/downsampling, compresión |
| Motor de búsqueda | Búsqueda de texto libre, facetas o filtros combinados sobre grandes volúmenes | Se usa como fuente de verdad transaccional | Fuente de verdad real, mecanismo y lag de sincronización, relevancia/ranking |
| Cache in-memory | Acelerar lecturas repetidas de datos ya persistidos en otro motor | Se usa como única fuente de verdad de datos que no pueden perderse | Política de invalidación, TTL, comportamiento ante cache miss/caída |
| Data warehouse analítico | Analítica histórica, BI o reporting agregado por lote, separado del OLTP | El caso necesita transacciones operativas de baja latencia | Frecuencia de carga/ETL, costo por consulta, separación del tráfico transaccional |
| Data lake / object storage | Ingesta masiva heterogénea para exploración o entrenamiento, sin transaccionalidad | Se necesita consulta transaccional de baja latencia o integridad referencial | Gobierno de esquema en lectura, catalogación, costo de vida útil de los datos |

## 5. Persistencia poliglota

Un bounded context puede combinar más de un motor cuando cada uno resuelve un patrón de acceso real — por ejemplo, un relacional como fuente de verdad más un motor de búsqueda para texto libre y una cache para sesión. En ese caso documenta en `16.xx`:

- cuál motor es la **fuente de verdad** y cuáles son réplicas/proyecciones derivadas;
- el mecanismo de sincronización (evento de dominio, CDC, dual write con reconciliación) y su lag tolerado;
- qué pasa si la réplica derivada se desincroniza o no está disponible (¿el caso de uso degrada o falla?).

No multipliques motores sin un patrón de acceso demostrado: cada motor adicional agrega operación, una ruta más de fallo y otra fuente de inconsistencia. Un CRUD simple no necesita documento + buscador + cache "por si acaso" — eso es sobre-ingeniería, igual que forzar CQRS o Hexagonal sin driver (`references/guia-catalogo-patrones.md`).

## 6. Validación mínima

| Pregunta de validación |
|---|
| ¿El patrón de acceso dominante del contenedor coincide con el tipo elegido, con evidencia de volumen/latencia/QPS esperados y no solo con la familiaridad del equipo? |
| ¿La consistencia elegida es la que exige el dominio, no la más fácil de operar? |
| Si hay 2 o más motores real y actualmente viables sin trade-off obvio, ¿se aplicó `references/guia-matriz-decision.md` citando las dimensiones de la sección 2? |
| Si hay persistencia poliglota, ¿está identificada la fuente de verdad y el mecanismo de sincronización de cada réplica? |
| ¿La decisión quedó registrada donde corresponde según la sección 7, en vez de quedar implícita en el nombre de una tecnología? |

## 7. Enrutamiento documental

| Situación | Comparación / selección | Aplicación materializada | Índice, decisión y auditoría |
|---|---|---|---|
| El tipo/motor cambia la topología o el costo a nivel de sistema (forma parte de una alternativa completa de `09`) | `09` compara dentro de la alternativa afectada | `14.xx`/`16.xx` del contenedor | `10` registra la selección; `20` enlaza; `25` audita |
| Decisión puntual de un contenedor, sin alternativa macro (ej. motor de BD de un microservicio) | Matriz ponderada de `references/guia-matriz-decision.md`, citando este catálogo como fuente de criterios | `16.xx` posee modelo, ER, consistencia, partición, PII/retención | Resultado corto como `DA-xxx` en `20-Decisiones-Arquitectonicas.md` |
| Mecanismo de sincronización entre motores (CDC, dual-write, proyección) es arquitectónicamente significativo | No aplica selección de tipo de BD | `14.xx`/`16.xx` documenta el mecanismo | Regístralo como táctica/patrón en `18-Tacticas-y-Patrones.md` si cruza varios contenedores o es un riesgo relevante |

`18` no indexa tipos ni motores de base de datos como si fueran un patrón: son una decisión tecnológica, no un mecanismo arquitectónico. Sí indexa, cuando sea significativo, el patrón/táctica que resuelve la sincronización entre motores (Sharding, CQRS, idempotencia, etc.) según `references/guia-catalogo-patrones.md`.

## 8. Validación experta con `dba`

Cuando el TO-BE (Caso A o C) define, cambia o retira persistencia —selección de motor en
`09`/`10`/`10.1`, `16`, cualquier `16.xx` o `16.xx.y`, servicios de datos en `17`, o una
migración de datos en `23`/`24`— y la skill `dba` está disponible, solicita su modo
`design-review` (y `data-migration` si aplica) **antes de `CP-03`** y otra vez si una
reapertura incremental cambia un `DATA-xxx`.

`dba` entrega `16.00-Revision-Experta-Datos_<Proyecto>.md` y
`16.00.1-Observaciones-Datos_<Proyecto>.json` con observaciones `DB-NNN` (severidad
`bloqueante`, `mayor`, `menor`, `nit` o `pregunta`). `dba` no edita `16.xx`; archi
conserva el ownership y **dispone cada observación** en el campo `disposition` del JSON:

| Disposición | Requisito |
|---|---|
| `incorporada` | El artefacto dueño (`16.xx`, `16.xx.y`, `17`, `20`) refleja el cambio y cita el `DB-NNN` |
| `rechazada-justificada` | `disposition_note` con la razón técnica verificable |
| `riesgo-aceptado` | `disposition_note` con autoridad, compensación y fecha; riesgo registrado en `21` |
| `diferida` | Solo para `menor`/`nit`; backlog o `21` |
| `pendiente` | Sin decisión todavía |

Reglas de cierre:

- `25` no puede declararse apto con un `DB-NNN` `bloqueante` o `mayor` en `pendiente` o
  `diferida`; `scripts/validate_architecture_coherence.py` lo comprueba si existe `16.00.1`.
- Las `pregunta` se responden en el artefacto dueño o se convierten en supuesto de `04`.
- Si `dba` no está disponible, `16` declara "Revisión experta de datos: No disponible —
  <motivo>" y se aplican las secciones 1–7 de esta guía; la ausencia no bloquea.
- `dba` puede validar después el resultado (`python <dba>/scripts/validate_findings.py
  16.00.1-Observaciones-Datos_<Proyecto>.json --archi`).
