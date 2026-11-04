# Guía: Modo multi-nube (Caso A sin proveedor definido)

Se activa dentro del Caso A (proyecto nuevo) cuando, tras leer el `.md` de especificaciones, no hay un proveedor de nube determinado para el despliegue.

> Todos los nombres de archivo de esta guía (los tres `.drawio`, `17.4-Pricing_<Proyecto>.md`, `17.5-Arquitectura_Costos_<Proyecto>.html`) se guardan dentro de `resources/architecture/`. Antes de generar los diagramas, valida/configura el MCP de diagramación siguiendo `references/guia-mcp-diagramacion.md`.

## Cómo decidir si el proveedor está definido

Antes de asumir que falta, revisa si el `.md` de specs ya lo resuelve de alguna de estas formas (cualquiera de ellas cuenta como "definido", no actives el modo multi-nube):
- Menciona explícitamente AWS, Azure o GCP (o un servicio propio de una de ellas, ej. "usar Cognito para auth" implica AWS).
- Declara una restricción técnica que lo determina indirectamente (ej. "el equipo ya opera todo en Azure", "debe integrar con Google Workspace/BigQuery").
- El usuario lo indica en la conversación aunque no esté en el `.md`.

Si nada de esto aparece y el sistema efectivamente se va a desplegar en la nube (no on-premise, no edge/IoT puro), el proveedor **no está definido** → activa este modo.

Si es ambiguo (ej. el proyecto podría ir on-premise o en la nube y no se aclara), pregúntale al usuario en vez de asumir — es el mismo criterio que ya aplica el Paso 0 del skill para otras ambigüedades.

## Qué produce este modo

En vez de un único diagrama en `17-Vista-de-Despliegue.md`, produce:

1. **Tres diagramas de despliegue**, uno por proveedor, en formato `.drawio` con iconografía oficial (ver `references/drawio-iconos-nube.md`) — la sub-numeración es fija por proveedor (ver "Convención de numeración de archivos" en `SKILL.md`), no por orden de generación:
   - `17.1-Despliegue_AWS_<Proyecto>.drawio`
   - `17.2-Despliegue_Azure_<Proyecto>.drawio`
   - `17.3-Despliegue_GCP_<Proyecto>.drawio`
2. **Un archivo de pricing comparativo**: `17.4-Pricing_<Proyecto>.md`.
3. **Un reporte HTML**: `17.5-Arquitectura_Costos_<Proyecto>.html`.
4. `17-Vista-de-Despliegue.md` enlaza los tres `.drawio`, el pricing y el reporte.

## Paso 1 — Traducir la arquitectura lógica a cada proveedor

Parte de la Vista de Contenedores (C4 Nivel 2) ya definida — es la misma para las tres nubes, lo que cambia es qué **servicio administrado concreto** implementa cada contenedor. Antes de mapear servicios revisa los patrones cloud seleccionados con `references/guia-catalogo-patrones.md`; conserva el mismo propósito y las mismas condiciones de validación en cada proveedor. Usa esta tabla de equivalencias como punto de partida (ajústala si el proyecto tiene necesidades específicas que descarten una opción):

| Necesidad del contenedor | AWS | Azure | GCP |
|---|---|---|---|
| Cómputo con gestión de servidor | EC2 (+ Auto Scaling) | Virtual Machines (+ VMSS) | Compute Engine (+ MIG) |
| Cómputo en contenedores, sin servidor | ECS Fargate | Container Apps / AKS | Cloud Run / GKE |
| Funciones (event-driven) | Lambda | Functions | Cloud Functions |
| API Gateway | API Gateway | API Management | API Gateway |
| Balanceo de carga | Application Load Balancer | Application Gateway / Load Balancer | Cloud Load Balancing |
| Base de datos relacional administrada | RDS (Postgres/MySQL) | Azure SQL Database / Database for PostgreSQL | Cloud SQL |
| Base de datos NoSQL | DynamoDB | Cosmos DB | Firestore |
| Cache en memoria | ElastiCache (Redis) | Azure Cache for Redis | Memorystore |
| Almacenamiento de objetos | S3 | Blob Storage | Cloud Storage |
| Colas / mensajería | SQS / SNS | Service Bus | Pub/Sub |
| CDN | CloudFront | Azure CDN / Front Door | Cloud CDN |
| Identidad de usuarios finales | Cognito | Azure AD B2C / Entra External ID | Identity Platform |
| Observabilidad | CloudWatch | Azure Monitor | Cloud Monitoring |

Elige siempre el equivalente más directo (mismo nivel de gestión: si el contenedor pide "sin servidor", no propongas VMs en ninguna nube). No optimices de más: el objetivo es una comparación justa, no la mejor arquitectura posible en cada nube por separado. En `17-Vista-de-Despliegue.md`, registra por cada `TP-xxx` cloud su alcance, mapeo por proveedor, failure domains, seguridad, observabilidad, costo, lock-in y evidencia/criterio de validación; no asumas que dos servicios equivalentes tienen idéntica semántica operativa.

## Paso 2 — Generar los tres diagramas

Para cada proveedor, sigue `references/drawio-iconos-nube.md` con los nombres reales del proyecto (no los genéricos de este documento). Mantén la topología equivalente entre los tres (mismos límites lógicos: red privada, subred pública/privada, zona de alta disponibilidad) para que la comparación sea legible.

## Paso 3 — Pricing

Sigue `references/guia-pricing-cloud.md` íntegro. Los servicios a cotizar en cada proveedor salen directamente de los nodos de cada diagrama del Paso 2.

Completa también `references/contrato-costos.md`: el inventario de `17` debe cubrir todos los ambientes por proveedor y los cargos compartidos, no solo la topología de producción. Crea `17.4.1-Costos_<Proyecto>.json` y genera los bloques de `17.4`/`17.5` desde sus partidas; no sumar alternativas de proveedor como gasto simultáneo.

## Paso 4 — Reporte HTML

Sigue `references/plantilla-reporte-costos.md`. Reutiliza el XML y las cifras de `17.4-Pricing_<Proyecto>.md`.

## Paso 5 — Enlazar todo desde el documento principal

En `17-Vista-de-Despliegue.md`, agrega una nota como:

> No se definió un proveedor de nube. Se evaluaron AWS, Azure y GCP — ver `17.1`, `17.2`, `17.3`, el comparativo `17.4-Pricing_<Proyecto>.md` y el reporte `17.5-Arquitectura_Costos_<Proyecto>.html`.

Y añade una recomendación explícita (no dejes la decisión abierta sin opinión): cuál de las tres conviene dado el contexto del proyecto (costo, requerimientos no funcionales, restricciones del equipo), y qué tendría que cambiar para que la recomendación cambiara.
