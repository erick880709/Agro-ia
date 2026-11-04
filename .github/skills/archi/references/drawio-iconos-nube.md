# Diagramas de despliegue cloud con catálogo curado (`.drawio`)

Esta guía aplica a `17.1-Despliegue_AWS_<Proyecto>.drawio`, `17.2-Despliegue_Azure_<Proyecto>.drawio` y `17.3-Despliegue_GCP_<Proyecto>.drawio`. El diagrama es un **resultado** del diseño aprobado; ni el catálogo de iconos ni una referencia visual deciden componentes, patrones, servicios o topología.

## Fuentes obligatorias

Antes de generar o editar un `.drawio`, lee:

- `assets/iconos/catalogo_iconos_curado.json`: fuente canónica de IDs, estilos y estado de los iconos permitidos.
- `assets/iconos/aliases_iconos.json`: resolución de nombres tecnológicos a IDs canónicos.
- `assets/iconos/catalogo_iconos.schema.json`: contrato de estructura del catálogo.
- `assets/drawio/referencia-despliegue-azure.drawio`: referencia **solo de composición visual** para Azure.
- `17-Vista-de-Despliegue.md`, `10.1-Arquetipo-Solucion.md`, vistas C4, decisiones y diseño detallado: fuentes de verdad de la arquitectura.

La referencia Azure fue abstraída del artefacto `resources/architecture/11.2-Despliegue_Azure_OCTO-HR.drawio`. No copies su topología, nombres, servicios ni relaciones. El archivo canónico actual se numera `17.2`; `11.2` es únicamente un antecedente visual del proyecto.

## Separación de responsabilidades

| Insumo | Sí determina | No determina |
|---|---|---|
| C4, `10.1`, decisiones y `17` | Componentes, servicios, relaciones, límites, ambientes, resiliencia y seguridad | Estilo gráfico |
| Catálogo curado | Icono, biblioteca, ruta/shape, alias, estado y fallback visual | Selección tecnológica |
| Referencia neutra | Jerarquía visual, espaciado, paleta, leyenda y lectura izquierda-derecha | Arquitectura del proyecto |

Regla: primero define el componente y el servicio con evidencia arquitectónica; después resuelve su representación en el catálogo. Nunca selecciones un servicio porque exista un icono disponible.

## Flujo de selección y generación

1. Construye el inventario de nodos y relaciones desde `17`, C4, diseño detallado, ADR y, cuando aplique, IaC.
2. Establece un solo proveedor por archivo. En una solución multicloud genera un archivo por proveedor y representa las integraciones externas entre ellos en `17`.
3. Resuelve cada servicio por alias normalizado en `aliases_iconos.json`; si no existe, consulta `aliases`, `displayName`, `category` y `tags` del catálogo.
4. Usa únicamente iconos con `status: active` y, de preferencia, `recommended: true`.
5. Copia el `style` canónico del icono y agrega al `mxCell` el atributo `archiIconId="<id-del-catalogo>"`.
6. Nombra el nodo con el componente real y su propósito, no solo con el producto cloud. Ejemplo: `API de Nómina · Azure App Service`.
7. Organiza límites reales: organización/cuenta/suscripción/proyecto, región, red, subred, zona, ambiente y trust boundary. No dibujes límites que no tengan soporte documental.
8. Etiqueta conexiones relevantes con protocolo, dirección y propósito; identifica flujos síncronos/asíncronos y límites de confianza.
9. Ejecuta el validador estricto antes de cerrar el artefacto.
10. Registra en `17` fecha, SHA-256, versión del catálogo, proveedor, resultado del validador y excepciones aprobadas.

## Bibliotecas permitidas

| Proveedor | Biblioteca actual | Mecanismo | Prohibido |
|---|---|---|---|
| Azure | `img/lib/azure2/...` | SVG oficial mediante `image=` | `img/lib/mscae/`, `mxgraph.azure.*` |
| AWS | `mxgraph.aws4.*` | `shape`/`resIcon` nativo | AWS3 o iconos de otro proveedor |
| GCP | `mxgraph.gcp3.*` | `shape` nativo | `mxgraph.gcp2.*` |

No mezcles bibliotecas de proveedores dentro de un archivo. Las cajas neutras se permiten para usuarios, sistemas externos, límites y anotaciones; no requieren `archiIconId` cuando no fingen ser un recurso cloud.

### Ejemplo Azure2

```xml
<mxCell id="api" archiIconId="azure.api-management"
  value="API pública · Azure API Management"
  style="shape=image;verticalLabelPosition=bottom;verticalAlign=top;imageAspect=1;aspect=fixed;html=1;image=img/lib/azure2/integration/API_Management_Services.svg;"
  vertex="1" parent="1">
  <mxGeometry x="300" y="180" width="72" height="72" as="geometry"/>
</mxCell>
```

### Ejemplo AWS4

```xml
<mxCell id="orders" archiIconId="aws.lambda"
  value="Procesador de pedidos · Lambda"
  style="sketch=0;outlineConnect=0;gradientColor=none;fillColor=#ED7100;strokeColor=#ffffff;verticalLabelPosition=bottom;verticalAlign=top;align=center;html=1;aspect=fixed;shape=mxgraph.aws4.resourceIcon;resIcon=mxgraph.aws4.lambda;"
  vertex="1" parent="1">
  <mxGeometry x="300" y="180" width="72" height="72" as="geometry"/>
</mxCell>
```

### Ejemplo GCP3

```xml
<mxCell id="web" archiIconId="gcp.cloud-run"
  value="Backend web · Cloud Run"
  style="sketch=0;html=1;verticalAlign=top;labelPosition=center;verticalLabelPosition=bottom;align=center;fontSize=11;fontStyle=0;fontColor=#000000;aspect=fixed;pointerEvents=1;shape=mxgraph.gcp3.cloudrun;"
  vertex="1" parent="1">
  <mxGeometry x="300" y="180" width="72" height="72" as="geometry"/>
</mxCell>
```

> **AWS4:** en `resourceIcon` el glifo se pinta con `strokeColor` y el fondo con `fillColor`. Con `strokeColor=none` el ícono sale como un cuadrado de color vacío. Copia siempre el `style` del catálogo (v1.1.0+), que usa `strokeColor=#ffffff` como la paleta oficial de draw.io.

### Ejemplo de conector

```xml
<mxCell id="e-api-db" value="SQL/TLS · lee y escribe"
  style="edgeStyle=orthogonalEdgeStyle;rounded=0;curved=0;html=1;endArrow=block;endFill=1;strokeColor=#42526E;exitX=1;exitY=0.5;exitDx=0;exitDy=0;entryX=0;entryY=0.5;entryDx=0;entryDy=0;"
  edge="1" parent="1" source="api" target="db">
  <mxGeometry relative="1" as="geometry">
    <Array as="points"><mxPoint x="520" y="216"/></Array>
  </mxGeometry>
</mxCell>
```

`source` y `target` deben existir; `curved=0` va explícito; los anclajes y waypoints se usan cuando el trazado automático atravesaría otro nodo (lo detecta `validate_drawio_layout.py`). Para asíncrono, identidad o telemetría agrega `dashed=1`.

## Contenedores y límites

Los límites (cuenta, región, red, subred, zona de confianza) son parte de la arquitectura, no decoración. Dibújalos con `container=1` y coloca los nodos como hijos (`parent=<id-del-contenedor>`), de modo que se muevan juntos y el validador detecte desbordes.

| Proveedor | Cómo dibujar el límite |
|---|---|
| AWS | Entradas `aws.group-*` del catálogo (`group-cloud`, `group-account`, `group-region`, `group-vpc`, `group-subnet-public`, `group-subnet-private`, `group-corporate-dc`), que reproducen los grupos oficiales de AWS4 y llevan `archiIconId`. |
| Azure | Caja neutra rotulada (`rounded=0;fillColor=none;dashed=1;strokeColor=#0078D4;verticalAlign=top;align=left;spacingLeft=10;container=1;`) con el ícono `azure.virtual-network` u otro del catálogo dentro, como en la referencia. Azure2 no trae shapes de grupo. |
| GCP | Caja neutra rotulada (`strokeColor=#4285F4`). La biblioteca GCP3 de draw.io no trae grupos ni íconos de Pub/Sub, Memorystore, Cloud Load Balancing o VPC: usa `gcp.generic-service` con el nombre real, o una excepción registrada. |

Las cajas neutras no llevan `archiIconId` porque no fingen ser un recurso cloud.

### Composición específica de AWS

- Anida límites de afuera hacia adentro: AWS Cloud → cuenta (si hay varias) → región → VPC → zona de disponibilidad → subred. Las zonas usan el rectángulo punteado de la paleta oficial (sin ícono, `strokeColor=#147EBA;dashed=1`) y se nombran con su identificador real (`us-east-1a`), no "AZ A".
- Servicios **globales** (CloudFront, Route 53, WAF asociado a CloudFront, IAM, Organizations) van dentro de AWS Cloud y fuera de la región. Servicios **regionales** sin VPC (S3, DynamoDB, ECR, CloudWatch, Secrets Manager, KMS, Lambda sin VPC) van dentro de la región y fuera de la VPC. Si dudas, la regla es: ¿se elige región al crearlo?
- Flujo de arriba hacia abajo: usuarios arriba; subredes públicas encima de las privadas; zonas lado a lado con el camino principal alineado en una columna por zona. El balanceador se ubica una sola vez sobre el borde entre zonas; NAT y otros elementos auxiliares hacia el exterior de cada zona.
- Recursos **implícitos obligatorios** (Internet Gateway cuando hay NAT o balanceador público, por ejemplo) se dibujan aunque la fuente no los mencione y se declaran en `17` como agregados. Recursos **opcionales** cuya presencia depende de una decisión (VPC endpoints, bastión, inspección) no se agregan sin decisión: se registran como pendientes.
- Para vistas de red o plataforma (`17.6.x`) usa los íconos de red del catálogo `1.2.0`: `aws.transit-gateway`, `aws.cloud-wan`, `aws.network-firewall`, `aws.nat-gateway`, `aws.internet-gateway`, `aws.vpc-endpoints`, `aws.direct-connect`, `aws.site-to-site-vpn`, `aws.route-53` y los de gobierno (`aws.organizations`, `aws.control-tower`, `aws.cloudtrail`, `aws.guardduty`, `aws.security-hub`).

## Fallback y excepciones

Si el servicio no tiene entrada exacta, usa primero el `fallback` genérico del proveedor y conserva el nombre real del servicio. No sustituyas por un icono semánticamente incorrecto.

Un SVG oficial nuevo o una imagen embebida solo se acepta cuando:

- no existe una entrada adecuada ni fallback suficiente;
- su fuente y términos de uso están verificados;
- el `mxCell` declara `archiIconException="<justificación breve>"`;
- la excepción, fuente, responsable y fecha de revisión quedan registradas en `17`;
- se propone incorporar el icono al catálogo en una versión posterior.

PNG incrustado se evita por calidad y mantenibilidad. Una captura o logo tomado de una página web no es un icono oficial aceptable.

## Validación determinista

Desde la raíz del repositorio:

```powershell
python .claude/skills/archi/scripts/validate_drawio_catalog.py --strict
python .claude/skills/archi/scripts/validate_drawio_catalog.py --drawio resources/architecture/17.2-Despliegue_Azure_<Proyecto>.drawio --provider azure --strict
```

La referencia neutra se valida excepcionalmente con `--reference`, porque conserva placeholders intencionales:

```powershell
python .claude/skills/archi/scripts/validate_drawio_catalog.py --drawio .claude/skills/archi/assets/drawio/referencia-despliegue-azure.drawio --provider azure --strict --reference
```

Después del catálogo valida la composición (conectores, solapamientos, contenedores, tamaños, leyenda):

```powershell
python .claude/skills/archi/scripts/validate_drawio_layout.py --drawio resources/architecture/17.2-Despliegue_Azure_<Proyecto>.drawio --strict
```

El cierre falla ante XML inválido, más de una página, placeholders en un entregable, biblioteca legada, mezcla de proveedor, `archiIconId` desconocido o diferencia entre el ID y el estilo. No uses `--reference` ni `--allow-multiple-pages` para aprobar un entregable del proyecto.

## Criterios visuales y arquitectónicos

- Una página por proveedor y ambiente representado; evita páginas ocultas o variantes sin decisión.
- Lectura principal izquierda-derecha: canales, edge, integración, aplicación, datos y operación.
- Límites y relaciones coinciden con C4 y `17`; no agregues servicios decorativos.
- Aplica la composición de `references/guia-calidad-visual-diagramas.md` §7: columnas por capa, grilla de 10 px, íconos de 64–78 px del mismo tamaño, contenedores anidados, conectores ortogonales etiquetados sin atravesar nodos, anclajes repartidos y leyenda.
- Expón zonas, redundancia, escalado, puntos de fallo, controles de red y observabilidad cuando sean relevantes.
- Distingue existente, nuevo, compartido, gestionado y fuera de alcance mediante etiqueta/leyenda, no alterando arbitrariamente los iconos oficiales.
- El XML debe quedar sin compresión para permitir revisión, diff y validación automática.

## Mantenimiento del catálogo

El catálogo fija repositorio, commit, versión de draw.io, archivos fuente y términos. Una actualización requiere:

1. verificar las fuentes oficiales fijadas;
2. actualizar solo entradas necesarias, alias y reemplazos;
3. incrementar `catalogVersion` con SemVer y `generatedAt`;
4. mantener IDs existentes o declararlos `deprecated` con `replacement`;
5. ejecutar el validador del catálogo y la referencia;
6. documentar el cambio en `release.md`.

No reemplaces el catálogo curado por un volcado masivo: el catálogo fuente puede servir para descubrimiento, pero solo pasan al catálogo canónico los iconos revisados y necesarios.
