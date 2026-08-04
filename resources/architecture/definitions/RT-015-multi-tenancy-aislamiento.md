# RT-015: Multi-Tenancy — Aislamiento de Datos

**Tipo:** Requisito técnico
**Categoría:** Arquitectura de datos / Seguridad
**Fuente:** RFP-AgroInteligente-Colombia.md — Secciones 5.2, 6.3, 13

## Descripción
La plataforma debe implementar un modelo de multi-tenancy que garantice el aislamiento estricto de datos entre clientes (agricultores). Cada cliente solo puede acceder a sus propios datos: fincas, análisis de suelo, reportes, conversaciones con el agente IA, datos de sensores.

El RFP deja abierta la decisión técnica entre tres enfoques:

1. **Row-Level Security (RLS):** todos los clientes comparten las mismas tablas de base de datos, pero políticas a nivel de fila en PostgreSQL garantizan que cada query solo retorne datos del cliente autenticado.
2. **Esquema por cliente:** cada cliente tiene un esquema separado en PostgreSQL, con tablas idénticas pero datos aislados.
3. **Base de datos por cliente:** cada cliente tiene su propia base de datos (máximo aislamiento, mayor costo operativo).

## Criterio medible / restricción concreta
- Verificación mediante pruebas de penetración: un cliente no puede acceder a datos de otro cliente manipulando IDs en la API.
- El mecanismo elegido debe ser transparente para los desarrolladores (no requerir lógica manual de filtrado en cada query).
- No especificados en el RFP — definir: enfoque concreto (se recomienda RLS para MVP, migrable a esquema por cliente si escala), ¿qué metadatos se comparten entre clientes (catálogo de cultivos, reglas agronómicas)?, ¿aplica también al agente IA (historial de conversaciones)?

## Impacto en la arquitectura
- Si RLS: políticas de seguridad en PostgreSQL, tenant_id en cada tabla, middleware que inyecta el tenant_id en las queries.
- Si esquema por cliente: lógica de routing de conexión en el backend, migraciones aplicadas a todos los esquemas.
- Si BD por cliente: mayor complejidad operativa (múltiples conexiones, backups individuales).
- Datos compartidos (catálogo de cultivos, reglas agronómicas) deben residir en un esquema o tabla común accesible para todos los clientes.

## Notas del analista
- **RLS en PostgreSQL** es la recomendación para el MVP: menor complejidad operativa, buen rendimiento para cientos de clientes, y migrable a esquema por cliente si la escala lo exige.
- El modelo de multi-tenancy también afecta al almacenamiento S3: los reportes y fotografías de fincas deben organizarse por tenant (prefijo de bucket).
- Los datos compartidos (reglas agronómicas, catálogo de cultivos, conocimiento del RAG) son multi-tenant por naturaleza y no requieren aislamiento.
- La Ley 1581 de 2012 (habeas data) en Colombia exige este aislamiento como requisito legal, no solo técnico.
