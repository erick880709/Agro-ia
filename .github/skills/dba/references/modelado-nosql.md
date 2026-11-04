# Modelado NoSQL

## Tabla de contenido

1. Principio: patrones de acceso primero
2. Plantilla de patrones de acceso
3. Por familia de motor
4. Consistencia y transacciones
5. Antipatrones
6. Checklist de revisión

## 1. Principio: patrones de acceso primero

En relacional se normalizan entidades y luego se consulta; en NoSQL se **listan las
consultas y se diseña la clave para cada una** ("start from the queries", ScyllaDB;
"evaluate access patterns before designing the schema", DynamoDB). Cambiar un patrón de
acceso después suele exigir migrar datos; por eso la tabla de patrones es un artefacto
obligatorio del diseño y de la revisión de archi.

## 2. Plantilla de patrones de acceso

| ID | Operación (`API-xxx-OP-xxx`/evento) | Tipo | Filtro / orden | Frecuencia y latencia | Volumen por respuesta | Estructura que la sirve | Consistencia |
|---|---|---|---|---|---|---|---|
| AP-01 | Movimientos de una cuenta por fecha desc | lectura | `cuenta_id`, rango de fecha | 300 rps, p99 < 50 ms | ≤ 50 | Tabla `PK=CUENTA#id`, `SK=MOV#fecha#id` | eventual aceptable |
| AP-02 | Registrar movimiento idempotente | escritura | `idem_key` | 100 rps | 1 | `Put` condicional sobre ítem `IDEM#key` en transacción | fuerte |

Sin fila que sirva un patrón, la revisión es `bloqueante` si el patrón está en ruta de
usuario (implicaría scan/filtro completo).

## 3. Por familia de motor

- **Clave-valor / documento ancho (DynamoDB):** partición por entidad de alta
  cardinalidad, clave de ordenamiento para rangos, single-table cuando las entidades se
  leen juntas, GSI para patrones secundarios (proyecciones mínimas), índices dispersos,
  TTL para expiración. Ver [DynamoDB](motores/dynamodb.md).
- **Documental (MongoDB, DocumentDB, Cosmos DB):** embeber lo que se lee y escribe junto
  y está acotado; referenciar lo que crece sin límite o se comparte; índices compuestos
  siguiendo ESR (igualdad, orden, rango); validación de esquema (`$jsonSchema`). Ver
  [MongoDB](motores/mongodb.md).
- **Columnar ancha (Cassandra, ScyllaDB, Keyspaces):** una tabla por consulta, partición
  acotada (bucketing por tiempo), clustering para orden, sin `ALLOW FILTERING`, TTL y
  compaction acorde. Ver [Cassandra/ScyllaDB](motores/cassandra-scylla.md).
- **Caché (Redis):** nunca fuente de verdad de lo que no puede perderse; TTL, invalidación
  y comportamiento ante fallo definidos.
- **Búsqueda (OpenSearch/Elasticsearch):** proyección de una fuente de verdad, con
  mecanismo de sincronización y lag declarados.
- **Grafo, series de tiempo, vectores:** ver [otros motores](motores/redis-busqueda-otros.md).

## 4. Consistencia y transacciones

Declara por patrón: lectura fuerte o eventual, aislamiento de escritura, transacciones
disponibles (DynamoDB `TransactWriteItems` hasta 100 ítems; MongoDB multi-documento en
replica set; LWT de Cassandra/Scylla de una partición) y su costo. Invariantes que cruzan
agregados se resuelven con escritura condicional, transacción acotada, saga u outbox; no
con lectura-luego-escritura sin condición.

## 5. Antipatrones

- Modelar NoSQL como tablas relacionales normalizadas y "hacer joins en la app".
- Clave de partición de baja cardinalidad o monótona (fecha, estado, tenant grande) →
  partición caliente.
- Colecciones/particiones sin límite (todos los eventos de un cliente en un ítem o
  partición).
- `Scan`/consulta sin clave en ruta de usuario; `ALLOW FILTERING`; `$where`/regex sin
  prefijo; `KEYS *` en Redis.
- Índices secundarios para todo (costo de escritura y almacenamiento).
- Usar el motor de búsqueda o la caché como fuente de verdad.

## 6. Checklist de revisión

- [ ] Tabla de patrones de acceso completa y trazada a `14.00`/`15`.
- [ ] Cada patrón servido por clave o índice; ningún scan en ruta de usuario.
- [ ] Distribución de partición analizada (cardinalidad, picos, tenants grandes).
- [ ] Tamaño máximo de ítem/documento/partición acotado.
- [ ] Consistencia y transacciones por patrón declaradas.
- [ ] TTL/retención, backups/PITR y costo estimados.
