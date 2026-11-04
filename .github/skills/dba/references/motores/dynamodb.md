# Amazon DynamoDB

Basado en el agente `dynamodb-expert` (0xfurai) y la práctica de diseño por patrones de
acceso. (Nota: los repositorios `DynamoDS/skills` y `ai-dynamo` no tratan de DynamoDB.)

## Tabla de contenido
1. Diseño de claves · 2. Índices · 3. Consistencia y transacciones · 4. Capacidad y costo ·
5. Límites · 6. Operación y seguridad · 7. Antipatrones

## 1. Diseño de claves
- Empieza por la [tabla de patrones de acceso](../modelado-nosql.md#2-plantilla-de-patrones-de-acceso).
- Clave de partición de alta cardinalidad y acceso uniforme (`CUENTA#<id>`, `CLIENTE#<id>`);
  clave de ordenamiento compuesta para rangos y jerarquías (`MOV#2026-11-02T10:00#<id>`).
- Single-table design cuando las entidades se leen juntas (item collections); tablas
  separadas cuando tienen ciclos de vida, capacidad o seguridad distintos — no es dogma.
- Escrituras de alto volumen sobre una sola clave → *write sharding* (sufijo aleatorio o
  calculado) y lectura agregada.

## 2. Índices
- GSI: patrón secundario, proyección mínima (`KEYS_ONLY`/`INCLUDE`), consistencia
  eventual, consume capacidad de escritura; índices dispersos para subconjuntos.
- LSI solo al crear la tabla y con límite de 10 GB por colección de ítems.
- Límites por tabla (GSI por defecto 20): no indexes "por si acaso".

## 3. Consistencia y transacciones
- Lecturas eventuales por defecto; `ConsistentRead` solo en tabla base/LSI (no GSI).
- Invariantes con `ConditionExpression` (`attribute_not_exists` para idempotencia,
  versión para bloqueo optimista).
- `TransactWriteItems` hasta 100 ítems, costo doble; idempotencia con `ClientRequestToken`.
- Streams para proyecciones, outbox y CDC; consumidores idempotentes.
- Global Tables: last-writer-wins; evita escrituras concurrentes al mismo ítem en
  distintas regiones.

## 4. Capacidad y costo
On-demand para tráfico impredecible; provisionado + auto scaling para estable. Observa
throttling (`ThrottledRequests`), particiones calientes (CloudWatch Contributor
Insights), tamaño de ítem (las unidades se cobran por 1 KB escritura / 4 KB lectura).
TTL para expiración sin costo de escritura.

## 5. Límites
Ítem ≤ 400 KB (datos grandes a S3 con puntero); respuesta de `Query`/`Scan` ≤ 1 MB por
página (paginar con `LastEvaluatedKey`); `BatchWriteItem` 25 ítems; `BatchGetItem` 100.

## 6. Operación y seguridad
PITR habilitado (35 días), backups bajo demanda para retenciones largas, cifrado con CMK
cuando se exige, `deletion_protection`, IAM por tabla/acción con condiciones
(`dynamodb:LeadingKeys` para aislar por tenant), VPC endpoint.

## 7. Antipatrones
`Scan` + `FilterExpression` en ruta de usuario; clave de partición por fecha/estado;
ítems que crecen sin límite (listas de movimientos dentro del ítem de cuenta); GSI sobre
atributo de baja cardinalidad; lectura-luego-escritura sin condición.
