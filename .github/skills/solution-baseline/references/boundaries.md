# Límites y responsabilidades

## Contrato organizacional

| Capacidad | Produce | No debe producir aquí |
|---|---|---|
| `archi` | Arquitectura aprobada, decisiones, `ARQ-xxx`, contratos, atributos de calidad, resolución de `architecture-gap` y la ubicación documentada del/los catálogo(s) de arquetipos gobernados (por ejemplo un catálogo en Backstage, un repositorio Git de arquetipos u otro registro aprobado) | Código baseline de los repositorios, selección de plantillas publicadas, o el contenido de los arquetipos mismos |
| `solution-baseline` | Blueprint, selección/creación gobernada de candidatos de arquetipo, baseline de aplicación, receipts y evidencia | Backlog funcional completo, DevOps, IaC, despliegue, ni el catálogo de arquetipos en sí: vive fuera del skill, en la fuente que documente `archi` |
| Genesis | Alias o entrada histórica para greenfield | Un proceso de bootstrap divergente |
| `builder` | Historias, módulos y comportamiento de negocio sobre una baseline válida | Replantear el arquetipo corporativo sin solicitud |
| `ranger` | Revisión independiente de calidad, riesgo y cumplimiento | Convertirse en writer concurrente durante generación |
| Vulcano / Vulcano Bob | CI/CD, IaC, imágenes/contenedores operacionales, cloud y despliegue | Estructura interna y código funcional de la aplicación |

## Artefactos permitidos

`solution-baseline` puede generar configuración de aplicación para ejecución local, `.env.example` sin secretos, health checks, telemetría de aplicación, contratos, documentación de desarrollo y el handoff a Vulcano (`vulcano-handoff.yaml`, subconjunto compatible con el vocabulario de Score: variables, health probes, puertos y dependencias externas por tipo, sin `image` ni aprovisionamiento).

No genera:

- Pipelines o workflows CI/CD.
- Terraform, Bicep, Pulumi, CloudFormation o módulos cloud.
- Dockerfiles, Compose, Helm, manifiestos Kubernetes o GitOps operacionales.
- Aprovisionamiento, secretos, despliegues, dashboards o alertas productivas.

Si un arquetipo incorpora esos archivos de forma inseparable, decláralo no elegible. Si ya existen en brownfield, consérvalos como `ignored` o `project_owned`; no los reclames ni los modifiques.

## Autoridad y aprobaciones

El permiso para crear código local no autoriza commits, push, creación de repositorios remotos, publicación de paquetes o arquetipos, ejecución de hooks no confiables ni cambios externos. Solicita autorización inmediatamente antes de cualquiera de esas acciones.

Cuando falte una decisión arquitectónica material, usa el contrato de [architecture-handoff.md](./architecture-handoff.md). Cuando solo falte un arquetipo compatible, el control permanece en `solution-baseline`.
