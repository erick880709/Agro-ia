# Redis, OpenSearch/Elasticsearch, grafos, series de tiempo y vectores

## Redis / ElastiCache / Azure Cache / MemoryDB
- Caché (cache-aside con TTL) o almacenamiento efímero; **fuente de verdad solo con
  MemoryDB/persistencia y decisión explícita**.
- TTL en todas las claves de caché; invalidación al escribir; protección contra *cache
  stampede* (locks, early refresh); comportamiento ante caída de Redis (degradar, no fallar).
- Sin `KEYS *` ni comandos O(N) en producción (`SCAN`); claves y valores pequeños; política
  de `maxmemory-policy` acorde.
- Cluster mode: claves relacionadas con hash tags `{}` para operaciones multi-clave.
- AUTH/ACL y TLS; sin exposición pública.

## OpenSearch / Elasticsearch
- Proyección de búsqueda, no fuente de verdad; sincronización por CDC/eventos con lag
  declarado y reindexación reproducible.
- Mapeos explícitos (no dynamic para campos críticos), tamaño de shard orientativo
  10–50 GB, ILM/ISM para retención, alias para reindexar sin downtime.
- Datos sensibles: minimizarlos en el índice; seguridad a nivel de índice/documento.

## Grafos (Neo4j, Amazon Neptune)
Cuando las consultas de relaciones profundas o variables (fraude, jerarquías, redes de
identidades) degradan con joins. Modelo de nodos/aristas guiado por consultas; índices
en propiedades de entrada; límites de profundidad en recorridos; carga y sincronización
desde la fuente de verdad. PostgreSQL con `WITH RECURSIVE` o extensiones de grafos puede
bastar para casos moderados.

## Series de tiempo (TimescaleDB, InfluxDB, Timestream)
Hipertablas/particiones por tiempo, compresión, políticas de retención y downsampling,
cardinalidad de etiquetas controlada.

## Vectores (pgvector, OpenSearch k-NN, ScyllaDB vector search, Azure DiskANN)
- Dimensión fija por modelo de embeddings; índice HNSW/IVFFlat/DiskANN según volumen y
  recall; métricas de distancia coherentes con el modelo.
- Filtrado por permisos/tenant **en la consulta** (antes o con el ANN), no después
  (fuga entre tenants; ver aegis LLM08).
- Re-embebido al cambiar de modelo: versionar la columna/índice.
- En sistemas con PostgreSQL ya existente, `pgvector` suele evitar un motor adicional.
