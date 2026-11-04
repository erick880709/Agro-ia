# Colector de métricas DORA

Condicional a `decisions.dora_collection_method: automated` en `resources/.vulcano/manifest.yaml`
(decisión de `vulcano`, ver `observability/01-monitoring.md`). Con `manual` o sin resolver, no
generar nada de esto — la sección "Métricas DORA" de `01-monitoring.md` sigue siendo la fuente,
solo que llenada a mano.

## Qué genera

```powershell
node .claude/skills/vulcano-bob/scripts/render-bob-dora.mjs --dora-cron "0 6 * * 1"
```

Con `decisions.pipeline_topology: per_component` (ver `orden-y-dependencias.md`), agregar
`--components <nombre1,nombre2,...>` — los mismos nombres usados para los pipelines de
aplicación (ej. `--components backend,frontend`). Sin este flag, el colector mide un único
componente implícito `app`, exactamente como antes de esta capacidad — no romper proyectos ya
generados con topología `single` es el motivo de este default.

```powershell
node .claude/skills/vulcano-bob/scripts/render-bob-dora.mjs --dora-cron "0 6 * * 1" --components backend,frontend
```

- `scripts/dora-collect.mjs` — colector genérico (mismo contenido en las tres plataformas, se
  autodetecta por variables de entorno: `GITHUB_ACTIONS`, `GITLAB_CI`, `TF_BUILD`). Expone
  `computeDoraMetrics(events)` y `parseComponents(raw)` como funciones puras, testables sin red.
  Con `DORA_COMPONENTS` (lista separada por comas) definida en el pipeline, mide cada componente
  por separado y escribe `{ generated_at, platform, window_days, components: { <nombre>: {...} } }`
  en vez del `{ ..., metrics: {...} }` de un solo componente — nunca un dataset combinado que
  oculte cuál componente cambia una métrica (mismo criterio que `observability/01-monitoring.md`
  exige cuando hay más de una unidad desplegable).
- Un pipeline programado por plataforma que ejecuta el colector y publica el dataset como
  artifact `dora-metrics-dataset`:

| Plataforma | Ruta | Requiere `--dora-cron` |
|---|---|---|
| `github_actions` | `.github/workflows/dora.yml` | Sí |
| `gitlab` | `.gitlab/ci/dora.yml` (standalone, no se incluye desde `.gitlab-ci.yml`) | No — GitLab programa el cron en la plataforma, no en el YAML |
| `azure_devops` | `infra/pipelines/dora.yml` | Sí |

## Fuente de datos por plataforma

El colector lee el historial de deployments a `prod` usando el token nativo del runtime — no
requiere un secreto adicional salvo Azure DevOps:

- **GitHub Actions**: Deployments API (`GET /repos/{repo}/deployments` +
  `.../deployments/{id}/statuses`) con `GITHUB_TOKEN` (automático). Requiere permiso
  `deployments: read` en el workflow (ya incluido en la plantilla).
- **GitLab**: Deployments API (`GET /projects/:id/deployments?environment=prod`) con
  `CI_JOB_TOKEN`. Verificar que el proyecto tenga habilitado el alcance de API para
  `CI_JOB_TOKEN` (Settings → CI/CD → Job token permissions) o sustituir por un project access
  token si no está disponible.
- **Azure DevOps**: Environment deployment records
  (`_apis/pipelines/environments/{environmentId}/environmentdeploymentrecords`) con
  `System.AccessToken`, mapeado explícitamente como `SYSTEM_ACCESSTOKEN` en el YAML (Azure
  Pipelines no lo expone como variable de entorno por defecto). **Este endpoint es relativamente
  reciente y su contrato ha cambiado entre versiones de Azure DevOps — verificar contra la
  documentación vigente antes de depender de este dato en producción**, mismo criterio que
  `references/estandares-operativos.md` aplica al resto del kit. Sin `--components`, requiere la
  variable operativa `prodEnvironmentId` (ID numérico del environment `prod`) en el variable group
  `vulcano-application-deploy`. Con `--components backend,frontend`, requiere en su lugar una
  variable `prodEnvironmentId<Nombre>` por componente (ej. `prodEnvironmentIdBackend`,
  `prodEnvironmentIdFrontend`) — cada Environment de Azure DevOps identifica el despliegue a
  `prod` de un solo componente, no puede compartirse entre ambos.
- **GitHub Actions / GitLab con `--components`**: el colector filtra por nombre de ambiente
  `prod-<componente>` en vez de `prod` — crear (o renombrar) los ambientes de despliegue de cada
  componente con ese patrón para que el filtro encuentre deployments.

## Métricas y sus aproximaciones declaradas

El colector calcula las cinco métricas vigentes sobre una ventana de `DORA_WINDOW_DAYS` días
(default 30) de deployments a `prod`:

| Métrica | Cómo se calcula | Aproximación declarada |
|---|---|---|
| Deployment frequency | despliegues exitosos / días de la ventana observada | — |
| Change lead time | promedio de `completed_at - started_at` por despliegue exitoso | Mide la duración del propio deployment, **no** el lead time real desde el commit/merge original — ese dato no está disponible sin correlacionar con el sistema de tareas |
| Failed deployment recovery time | promedio de tiempo entre un despliegue fallido y el siguiente exitoso | — |
| Change fail rate | despliegues fallidos / total de despliegues | — |
| Deployment rework rate | % de despliegues exitosos consecutivos separados por ≤ `DORA_REWORK_WINDOW_HOURS` (default 24h) | Aproxima "rework" por proximidad temporal, no por relación causal real entre despliegues |

Si la ventana no tiene deployments, todas las métricas quedan `null` con `sample_size: 0` — el
colector nunca infiere un valor desde cero datos. El dataset resultante (`dora-metrics.json`) es
la fuente citable que `observability/01-monitoring.md` debe referenciar en su tabla de métricas
DORA, incluyendo la nota de aproximación de cada campo.

## Registro en el manifiesto de Bob (manual)

`bob-manifest.yaml` no incluye este artefacto por defecto — es condicional. Al generarlo:

1. Agregar `pipeline.dora_pipeline.path` (ver tabla arriba) a `target_repo.pipeline_files`, para
   que `validate-vulcano-bob.mjs` lo valide con las mismas reglas semánticas que el resto de
   pipelines de esa plataforma.
2. Agregar una entrada `pipeline-dora` a `artifacts`, con la misma forma que `pipeline-drift`
   (mismo `depends_on`, sin inputs de ambiente porque no despliega nada), para poder cerrarla con
   `validate-and-record-bob-artifact.mjs --logical-id pipeline-dora` — el prefijo `pipeline-`
   reutiliza la validación semántica de pipelines ya existente, sin necesitar un adaptador nuevo.
