# Diagramas de despliegue con iconografía real (.drawio)

Cuando el proveedor de nube de despliegue es AWS, Azure o GCP, el diagrama de despliegue (sección 12 de la plantilla) se genera como archivo **`.drawio`** (formato diagrams.net / mxGraph), no como Mermaid. Esto permite usar los **iconos oficiales de cada proveedor** en vez de cajas genéricas.

> Antes de generarlo, valida/configura la herramienta MCP `drawio-remoto` siguiendo `references/guia-mcp-diagramacion.md` — si está disponible, úsala para crear/editar el archivo en vez de escribir el XML a mano (esta guía sigue sirviendo como referencia de nombres de shape, colores y como fallback manual). El archivo resultante se guarda dentro de `resources/architecture/` — créala si no existe.

## Por qué .drawio y no Mermaid para este diagrama

draw.io/diagrams.net trae **shape libraries nativas y oficiales** de AWS, Azure y GCP (se actualizan junto con los proveedores). Esto significa que en la mayoría de los casos **no necesitas ningún archivo de icono subido por el usuario**: basta con usar el nombre de shape correcto en el atributo `style` de cada `mxCell`. Los paquetes de iconos que suba el usuario (`assets/icons/<proveedor>/`) se usan solo como **fallback** para servicios muy nuevos o de nicho que la librería nativa de draw.io todavía no cubra (ver sección "Fallback a iconos subidos por el usuario").

## Estructura base de un archivo .drawio

Todo archivo es XML con esta forma. Cambia `id`, `value`, `style` y `geometry` por cada nodo; una `mxCell` con `edge="1"` por cada conexión.

```xml
<mxfile host="app.diagrams.net">
  <diagram name="Despliegue AWS - [Nombre Proyecto]" id="despliegue-aws">
    <mxGraphModel dx="1200" dy="800" grid="1" gridSize="10" guides="1" tooltips="1" connect="1" arrows="1" fold="1" page="1" pageScale="1" pageWidth="1100" pageHeight="850" math="0" shadow="0">
      <root>
        <mxCell id="0" />
        <mxCell id="1" parent="0" />

        <!-- Ejemplo: nodo de icono AWS (EC2) -->
        <mxCell id="ec2_api" value="API de Pedidos" style="sketch=0;outlineConnect=0;fontColor=#232F3E;gradientColor=none;fillColor=#ED7100;strokeColor=none;dashed=0;verticalLabelPosition=bottom;verticalAlign=top;align=center;html=1;fontSize=12;fontStyle=0;aspect=fixed;shape=mxgraph.aws4.resourceIcon;resIcon=mxgraph.aws4.ec2;" vertex="1" parent="1">
          <mxGeometry x="360" y="200" width="78" height="78" as="geometry" />
        </mxCell>

        <!-- Ejemplo: grupo/contenedor (VPC) -->
        <mxCell id="vpc1" value="VPC - prod (10.0.0.0/16)" style="points=[[0,0],[0.25,0],[0.5,0],[0.75,0],[1,0],[1,0.25],[1,0.5],[1,0.75],[1,1],[0.75,1],[0.5,1],[0.25,1],[0,1],[0,0.75],[0,0.5],[0,0.25]];outlineConnect=0;gradientColor=none;html=1;whiteSpace=wrap;fontSize=12;fontStyle=0;container=1;pointerEvents=0;collapsible=0;recursiveResize=0;shape=mxgraph.aws4.group;grIcon=mxgraph.aws4.group_vpc;strokeColor=#248814;fillColor=none;verticalAlign=top;align=left;spacingLeft=30;fontColor=#AAB7B8;dashed=0;" vertex="1" parent="1">
          <mxGeometry x="120" y="120" width="560" height="360" as="geometry" />
        </mxCell>

        <!-- Ejemplo: conexión -->
        <mxCell id="edge1" style="edgeStyle=orthogonalEdgeStyle;rounded=0;html=1;endArrow=block;" edge="1" parent="1" source="ec2_api" target="rds_db">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>
      </root>
    </mxGraphModel>
  </diagram>
</mxfile>
```

Reglas prácticas:
- Un solo `<diagram>` por archivo `.drawio` (un proveedor = un archivo). Si generas los 3 proveedores en modo comparación, produce 3 archivos: `Despliegue_AWS_<Proyecto>.drawio`, `Despliegue_Azure_<Proyecto>.drawio`, `Despliegue_GCP_<Proyecto>.drawio`.
- Agrupa visualmente por límites lógicos reales: VPC/Resource Group/Proyecto, subred pública vs privada, región/zona de disponibilidad.
- Usa `fillColor` acorde a la paleta de cada proveedor (ver tablas abajo) — no inventes colores.
- Nombra cada nodo con el nombre real del componente del sistema (ej. "API de Pedidos"), no el nombre genérico del servicio ("EC2 Instance").

## Tabla de shapes — AWS (librería `mxgraph.aws4`)

| Servicio | `shape` / `resIcon` | Color `fillColor` |
|---|---|---|
| EC2 (instancia/ASG) | `resIcon=mxgraph.aws4.ec2` | `#ED7100` |
| ECS / Fargate | `resIcon=mxgraph.aws4.fargate` / `mxgraph.aws4.elastic_container_service` | `#ED7100` |
| Lambda | `resIcon=mxgraph.aws4.lambda` | `#ED7100` |
| Elastic Load Balancer / ALB | `resIcon=mxgraph.aws4.application_load_balancer` | `#8C4FFF` |
| API Gateway | `resIcon=mxgraph.aws4.api_gateway` | `#E7157B` |
| RDS | `resIcon=mxgraph.aws4.relational_database_service` | `#527FFF` |
| DynamoDB | `resIcon=mxgraph.aws4.dynamodb` | `#527FFF` |
| ElastiCache (Redis) | `resIcon=mxgraph.aws4.elasticache` | `#527FFF` |
| S3 | `resIcon=mxgraph.aws4.simple_storage_service` | `#7AA116` |
| SQS | `resIcon=mxgraph.aws4.simple_queue_service` | `#E7157B` |
| SNS | `resIcon=mxgraph.aws4.simple_notification_service` | `#E7157B` |
| CloudFront | `resIcon=mxgraph.aws4.cloudfront` | `#8C4FFF` |
| VPC (contenedor) | `shape=mxgraph.aws4.group;grIcon=mxgraph.aws4.group_vpc` | `#248814` |
| Subred pública/privada | `shape=mxgraph.aws4.group;grIcon=mxgraph.aws4.group_security_group` | `#248814` |
| Route 53 | `resIcon=mxgraph.aws4.route_53` | `#8C4FFF` |
| Cognito | `resIcon=mxgraph.aws4.cognito` | `#DD344C` |
| CloudWatch | `resIcon=mxgraph.aws4.cloudwatch` | `#E7157B` |

Patrón de `style` completo para cualquier icono de recurso AWS4 (solo cambia `resIcon` y `fillColor`):
```
sketch=0;outlineConnect=0;fontColor=#232F3E;gradientColor=none;fillColor=<COLOR>;strokeColor=none;dashed=0;verticalLabelPosition=bottom;verticalAlign=top;align=center;html=1;fontSize=12;fontStyle=0;aspect=fixed;shape=mxgraph.aws4.resourceIcon;resIcon=<RESICON>;
```

## Tabla de shapes — Azure (librería `mxgraph.azure`)

| Servicio | `shape` | Color `fillColor` |
|---|---|---|
| Virtual Machine | `mxgraph.azure.virtual_machine` | `#0078D4` |
| App Service | `mxgraph.azure.app_services` | `#0078D4` |
| AKS (Kubernetes Service) | `mxgraph.azure.kubernetes_services` | `#0078D4` |
| Functions | `mxgraph.azure.function_apps` | `#0078D4` |
| Application Gateway / Load Balancer | `mxgraph.azure.load_balancers` | `#0078D4` |
| API Management | `mxgraph.azure.api_management_services` | `#0078D4` |
| Azure SQL Database | `mxgraph.azure.sql_database` | `#0078D4` |
| Cosmos DB | `mxgraph.azure.azure_cosmos_db` | `#0078D4` |
| Azure Cache for Redis | `mxgraph.azure.cache_redis` | `#0078D4` |
| Blob Storage | `mxgraph.azure.storage_accounts` | `#0078D4` |
| Service Bus (colas) | `mxgraph.azure.service_bus` | `#0078D4` |
| Azure CDN / Front Door | `mxgraph.azure.cdn_profiles` | `#0078D4` |
| Virtual Network (contenedor) | `mxgraph.azure.virtual_networks` | `#0078D4` |
| Azure AD / Entra ID | `mxgraph.azure.azure_active_directory` | `#0078D4` |
| Azure Monitor | `mxgraph.azure.monitor` | `#0078D4` |

Patrón de `style` para íconos Azure (estilo plano oficial):
```
sketch=0;points=[[0,0,0],[0.25,0,0],[0.5,0,0],[0.75,0,0],[1,0,0],[0,1,0],[0.25,1,0],[0.5,1,0],[0.75,1,0],[1,1,0],[0,0.25,0],[0,0.5,0],[0,0.75,0],[1,0.25,0],[1,0.5,0],[1,0.75,0]];outlineConnect=0;fontColor=#232F3E;gradientColor=none;fillColor=<COLOR>;strokeColor=none;dashed=0;verticalLabelPosition=bottom;verticalAlign=top;align=center;html=1;fontSize=12;fontStyle=0;aspect=fixed;shape=<SHAPE>;
```

## Tabla de shapes — GCP (librería `mxgraph.gcp2`)

| Servicio | `shape` | Color `fillColor` |
|---|---|---|
| Compute Engine | `mxgraph.gcp2.compute_engine` | `#4285F4` |
| GKE (Kubernetes Engine) | `mxgraph.gcp2.kubernetes_engine` | `#4285F4` |
| Cloud Functions | `mxgraph.gcp2.cloud_functions` | `#4285F4` |
| Cloud Run | `mxgraph.gcp2.cloud_run` | `#4285F4` |
| Cloud Load Balancing | `mxgraph.gcp2.cloud_load_balancing` | `#4285F4` |
| API Gateway | `mxgraph.gcp2.api_gateway` | `#4285F4` |
| Cloud SQL | `mxgraph.gcp2.cloud_sql` | `#4285F4` |
| Firestore | `mxgraph.gcp2.firestore` | `#4285F4` |
| Memorystore (Redis) | `mxgraph.gcp2.memorystore` | `#4285F4` |
| Cloud Storage | `mxgraph.gcp2.cloud_storage` | `#4285F4` |
| Pub/Sub | `mxgraph.gcp2.pubsub` | `#4285F4` |
| Cloud CDN | `mxgraph.gcp2.cloud_cdn` | `#4285F4` |
| VPC (contenedor) | `mxgraph.gcp2.virtual_private_cloud` | `#4285F4` |
| Identity Platform | `mxgraph.gcp2.identity_platform` | `#4285F4` |
| Cloud Monitoring | `mxgraph.gcp2.cloud_monitoring` | `#4285F4` |

> Los nombres exactos de shape de Azure y GCP pueden variar levemente entre versiones de draw.io. Si al abrir el archivo un icono no se renderiza (aparece como caja gris con signo de interrogación), es la señal para: 1) verificar el nombre exacto abriendo la librería correspondiente en draw.io Desktop/Web y copiando su `style`, o 2) usar el fallback de imagen (siguiente sección).

## Fallback: iconos subidos por el usuario

Si el usuario cargó paquetes oficiales de iconos en `assets/icons/aws/`, `assets/icons/azure/` o `assets/icons/gcp/` (SVG/PNG individuales, no capturas de pantalla), úsalos solo cuando:
1. El servicio no tiene shape nativo en draw.io, o
2. El usuario pide explícitamente una versión/estilo de icono distinta a la nativa.

Para insertar un icono como imagen en vez de shape nativo:
```xml
<mxCell id="custom_icon" value="Nombre del Componente" style="shape=image;verticalLabelPosition=bottom;verticalAlign=top;imageAspect=1;aspect=fixed;image=data:image/svg+xml,<SVG_BASE64_O_URLENCODED>;" vertex="1" parent="1">
  <mxGeometry x="100" y="100" width="64" height="64" as="geometry" />
</mxCell>
```
Incrusta el SVG (preferido sobre PNG por escalabilidad) codificado en el atributo `image`, para que el `.drawio` siga siendo un archivo único y portable sin dependencias externas.

## Al generar el archivo

1. Verifica que el XML sea válido (cierres de tags correctos, sin caracteres sin escapar como `<`, `>`, `&` dentro de atributos `value` — usa entidades `&lt;`, `&gt;`, `&amp;`).
2. Guarda con extensión `.drawio` junto al documento de arquitectura, referenciado desde la sección 12 con una nota: *"Ver `Despliegue_<Proveedor>_<Proyecto>.drawio` — ábrelo en https://app.diagrams.net o la extensión de VS Code draw.io.integration"*.
3. El mismo XML (el contenido de `<mxGraphModel>...</mxGraphModel>`) se reutiliza tal cual para embeberlo en el reporte HTML (ver `references/plantilla-reporte-costos.md`), evitando mantener dos versiones del diagrama.
