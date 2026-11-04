# Fronteras y fuentes

## Autoridad por tipo de información

| Información | Fuente que corresponde |
|---|---|
| Comportamiento deseado | Requisitos/decisiones aceptados y mandato del usuario |
| Arquitectura de sistema | ADR y arquitectura vigentes; responsable arquitectónico |
| Compatibilidad externa | Contratos publicados y consumidores reales |
| Apariencia visual, componentes y assets de marca | Sistema de diseño del proyecto (tokens, catálogo de componentes, manifiesto de assets) |
| Estado observado | Código, configuración y ejecución comprobada |
| Detalle de implementación | Decisión local de Builder compatible con las anteriores |

Las instrucciones aplicables de la sesión y del repositorio gobiernan el trabajo.
Un archivo recién generado no desplaza una fuente aprobada solo por ser más nuevo.
Si la documentación falta, registra observaciones relevantes en el expediente del
cambio; no crees automáticamente una arquitectura global supuestamente aprobada.

## Baseline y ownership

Lee receipt/handoff si existen. Aplica su política real; si falta ownership sobre
una zona gestionada, no lo inventes:

- `project_owned` y `generated_once` transferido: cambia dentro del encargo,
  preservando ediciones existentes; no significa que Builder deba ignorar código.
- `extendable`: utiliza los puntos de extensión declarados.
- `managed`: usa una extensión permitida o devuelve reconcile/upgrade al flujo
  propietario; no edites el archivo y luego actualices su hash para ocultarlo.
- `ignored`: respeta la exclusión; si el encargo requiere esa ruta, resuelve la
  contradicción de alcance antes de acceder/modificar contra esa política.

Cambios superpuestos con trabajo local requieren lectura y adaptación. Si no puedes
preservar ambos propósitos, presenta el conflicto concreto; no sobrescribas ni
descartes contenido para facilitar la tarea. Un árbol sucio no es por sí solo bloqueo.

## Handoffs condicionales

| Necesidad que excede el cambio local | Destino si existe |
|---|---|
| Ambigüedad de producto | Fuente responsable / Epicureo |
| Estados y reglas de dominio no resueltos | Responsable de dominio / Storming |
| Topología, stack o límites materiales | Responsable de arquitectura / Archi |
| Diseño de interacción amplio | Responsable UX / Iris |
| Componente, variante, token o asset de marca faltante | Responsable UX / sistema de diseño (Iris) |
| Crear baseline o reconciliar archivos gestionados | Solution Baseline |
| Revisión independiente del diff antes de cerrar | code-review |
| Evaluación de calidad especializada | QA / Ranger |
| IaC, pipelines, despliegue u operación | Flujo Vulcano / responsable operacional |
| Subir la directiva `go`, el `toolchain` o la imagen base de Go | Responsable de plataforma o arquitectura |
| `ng update`, cambio de runner, zone.js ↔ zoneless, SSR, micro-frontends o presupuestos de bundle | Responsable de arquitectura frontend |
| Subir Java, Spring Boot o el plugin del Scaffold (`./gradlew u`), cambiar de imperativo a reactivo o añadir un módulo de infraestructura con tecnología nueva | Responsable de arquitectura backend |

No todas las organizaciones tienen esos skills. Entrega un gap con fuente,
decisión requerida, componentes afectados y trabajo que puede continuar. No
invoques capacidades inexistentes ni hagas del ecosistema local una dependencia
obligatoria de Builder. Un handoff no autoriza ejecutar operaciones remotas.

Las decisiones internas de una feature que respeten límites existentes no necesitan
un ciclo de arquitectura. No amplíes un cambio a bootstrap, migración de stack o
reorganización de repositorios porque falte un módulo de referencia.
