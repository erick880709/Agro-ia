# MongoDB, Amazon DocumentDB y Azure Cosmos DB

## Tabla de contenido
1. Modelado · 2. Índices · 3. Consistencia y transacciones · 4. Compatibilidad entre servicios · 5. Operación

## 1. Modelado
- Embeber lo que se lee/escribe junto, es acotado y pertenece al agregado; referenciar lo
  que crece sin límite (movimientos, eventos), se comparte o se actualiza independiente.
- Documento ≤ 16 MB, pero el objetivo práctico es mucho menor; arrays sin límite son
  antipatrón (patrones bucket/outlier/subset).
- `$jsonSchema` con `validationLevel: strict` para colecciones críticas; campo
  `schemaVersion` para evolución.
- Dinero en `Decimal128`; fechas en `Date` (UTC).

## 2. Índices
Regla ESR (Equality, Sort, Range); índices compuestos que cubren; `unique` para
invariantes; parciales; TTL; evita `$regex` sin prefijo anclado, `$where`, `$ne`/`$nin`
como filtro principal; `explain("executionStats")` sin `COLLSCAN` en rutas de usuario;
índices declarados explícitamente (no `autoIndexCreation` en prod con Spring Data).

## 3. Consistencia y transacciones
`writeConcern: { w: "majority" }` para datos que no pueden perderse; `readConcern`
`majority`/`snapshot` según necesidad; transacciones multi-documento (replica set) cortas;
preferir atomicidad de un documento con operadores (`$inc`, `findOneAndUpdate` condicional).

## 4. Compatibilidad entre servicios
- **DocumentDB:** compatible con la API de MongoDB por versión, con diferencias
  (operadores, índices, transacciones, change streams): verifica cada funcionalidad.
- **Cosmos DB:** modelo de costos por RU, clave de partición obligatoria y crítica
  (inmutable), niveles de consistencia (strong, bounded staleness, session, consistent
  prefix, eventual); API NoSQL vs API para MongoDB con capacidades distintas.

## 5. Operación
Backups continuos/PITR del servicio, réplicas en varias zonas, oplog window suficiente
para ventanas de mantenimiento/CDC, monitoreo de `WiredTiger cache`, conexiones y
consultas lentas (profiler), autenticación y TLS obligatorios.
