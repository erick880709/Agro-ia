# Guía de Evidencia en Video (Playwright)

Cómo grabar, conservar, organizar y reportar los videos de ejecución de
pruebas para que cada caso del runbook tenga evidencia trazable y revisable.

---

## Índice

- [Política de Grabación](#política-de-grabación)
- [Configuración de Playwright](#configuración-de-playwright)
- [Legibilidad del Video (por qué se ve acelerado)](#legibilidad-del-video-por-qué-se-ve-acelerado)
- [Estructura de Carpetas](#estructura-de-carpetas)
- [Convención de Id de Caso](#convención-de-id-de-caso)
- [Generar el Reporte Después de una Ejecución](#generar-el-reporte-después-de-una-ejecución)
- [Subida de Artefactos en CI](#subida-de-artefactos-en-ci)
- [Almacenamiento y Retención](#almacenamiento-y-retención)
- [Solución de Problemas](#solución-de-problemas)

---

## Política de Grabación

Según la [política QA compartida](../../../contracts/output/validators/qa/qa-policy.json),
por defecto para navegador: **grabar cada prueba, en cada ejecución, y
conservar cada video** — no solo los que fallan. Esto da evidencia de
auditoría completa por ejecución, a costa del uso de disco. Se aplica así:

| Prioridad | Video | Trace | Screenshot |
|---|---|---|---|
| Critical / High | Siempre activado, siempre conservado | Siempre activado | Siempre activado |
| Medium / Low | Siempre activado, siempre conservado | Siempre activado | Siempre activado |

Solo si el encargo pide explícitamente reducir la evidencia, registra la
excepción y su motivo en `data.evidencePolicy.override`. Una opción es `video: 'retain-on-failure'` en
`playwright.config.ts` (sin borrar los videos de casos críticos) —
comunicá esto explícitamente al usuario antes de cambiar el valor por
defecto, ya que cambia lo que los auditores pueden ver después de los hechos.

## Configuración de Playwright

Usá `../templates/project/playwright.config.ts` (de `qa-ranger-playwright`) como base. Bloque relevante:

```typescript
use: {
  video: { mode: 'on', size: { width: 1280, height: 720 } },
  trace: 'on',
  screenshot: 'on',
},
```

Notas:
- `video` es una opción a **nivel de contexto**: solo aplica a los
  contextos de navegador creados después de que la config/fixture la
  establece. No intentes alternarla a mitad de una prueba.
- Un `size` fijo mantiene los videos chicos y consistentes; sin eso,
  Playwright escala al viewport, lo que puede producir tamaños de archivo
  inconsistentes entre specs.
- Grabar en modo headless está totalmente soportado y es el default en CI;
  no hace falta `headless: false` para obtener video.

## Legibilidad del Video (por qué se ve acelerado)

Playwright graba el video en tiempo real de ejecución: si el test hace clic,
tipea y navega sin ninguna pausa deliberada, el video muestra esas acciones
a la velocidad real (muy rápida) a la que corre el navegador, sin transición
visible entre pasos. El resultado es un video técnicamente correcto pero
inútil para que una persona entienda qué se probó. Dos ajustes lo resuelven
juntos:

**1. `slowMo` — pausa entre acciones.** `../templates/project/playwright.config.ts`
ya lo trae configurado vía la variable de entorno `QA_SLOWMO_MS`:

```typescript
const SLOWMO_MS = Number(process.env.QA_SLOWMO_MS ?? 300);

export default defineConfig({
  use: {
    launchOptions: {
      slowMo: SLOWMO_MS,
    },
  },
});
```

`slowMo` agrega una demora fija (en ms) antes de cada acción de Playwright,
tanto en modo headed como headless — no afecta las aserciones ni introduce
no-determinismo, solo espacia las acciones en el tiempo para que el video
se pueda seguir. Guía de valores (variable `QA_SLOWMO_MS` en `.env.qa`):

| Valor | Cuándo usarlo |
|---|---|
| `0` | Gate de CI puramente funcional, donde nadie va a mirar el video, y la velocidad de la suite importa más que la legibilidad. |
| `250`-`400` (default `300`) | Evidencia de ejecución estándar: legible para un humano sin alargar demasiado la suite. |
| `600`+ | Video pensado para demo/presentación a stakeholders, no para un gate de CI. |

Si subís mucho `QA_SLOWMO_MS`, un test con muchos pasos puede superar el
timeout por defecto de Playwright; la plantilla ya escala el `timeout`
global en función de `SLOWMO_MS` para cubrir ese caso.

**2. `test.step()` — puntos de referencia nombrados.** `slowMo` hace que el
video se pueda seguir, pero no le dice a quien lo mira *qué* está pasando
en cada momento. Envolver los pasos lógicos del test en `test.step()` los
etiqueta en el reporte HTML y en el trace viewer de Playwright, así se
puede saltar directo a "llenar formulario de pago" en vez de scrubear todo
el video a ciegas:

```typescript
test('TC-01 [critical] - Login con credenciales válidas', async ({ page }) => {
  await test.step('Abrir la página de login', async () => {
    await page.goto('/login');
  });

  await test.step('Completar credenciales', async () => {
    await page.getByLabel('Email').fill(process.env.QA_USER_EMAIL!);
    await page.getByLabel('Password').fill(process.env.QA_USER_PASSWORD!);
  });

  await test.step('Enviar y verificar redirección', async () => {
    await page.getByRole('button', { name: 'Sign in' }).click();
    await expect(page).toHaveURL('/dashboard');
  });
});
```

Regla práctica: si un caso tiene más de 3-4 acciones de UI, dividilo en
`test.step()` con nombres que describan la intención (no la acción cruda:
"Completar credenciales", no "fill inputs").

## Estructura de Carpetas

Todo vive bajo `resources/qa/` en la raíz del proyecto (ver
`../../ranger/SKILL.md#estructura-de-entregables-carpeta-de-salida`). Si alguna de
estas carpetas no existe, creala antes de escribir el primer archivo ahí.

Cada ejecución tiene su `runId`. El reporter incluido copia los adjuntos de
Playwright por caso, proyecto e intento. El paquete `playwright-ctrf-json-reporter`
escribe el CTRF con las rutas de esas copias, incluidos los intentos anteriores:

```
resources/qa/
├── TC-01/<runId>/
│   ├── chromium/
│   │   ├── attempt-0/                 # video.webm, trace.zip, screenshot-0.png
│   │   └── attempt-1/                 # primer reintento
│   └── firefox/
│       └── attempt-0/
├── test-results/<runId>/              # originales del runner; no se borran
└── reports/<runId>/
    ├── ctrf.json                        # resultado final y adjuntos de todos los intentos
    ├── html/
    └── execution-report.md
```

La plantilla toma `<runId>` de `QA_RUN_ID` o genera un UUID (timestamp, ej.
`2026-07-08T14-30-00Z`, o un número de build de CI también sirven). Nunca
reutilices un `runId` entre ejecuciones distintas: la evidencia anterior quedaría
mezclada con la nueva.
No necesitas ejecutar un organizador después de las pruebas ni generar un manifest.
Los adjuntos se copian cuando están disponibles y al finalizar cada intento.
Así, los adjuntos en memoria también pueden incluirse en los blobs de CI.
Un error de copia se conserva como
error global en CTRF y fuerza un código de salida fallido. Si falta ID, los adjuntos
se conservan bajo `SIN-ID-<hash>`; eso no acredita trazabilidad al plan.
Los nombres que no pueden usarse como carpeta o que colisionan por mayúsculas
reciben un hash para conservar su identidad también en Windows.
Los adjuntos previos aparecen en CTRF con nombres como `attempt-0/video`.
Los adjuntos duplicados reciben un sufijo numérico, sin sobrescribir archivos.
Entrega `resources/qa/` manteniendo sus rutas para que los enlaces sigan funcionando.
El reporter usa `projectRoot` como raíz, comprueba los destinos y rechaza enlaces
o junctions en las carpetas de salida. Si no puede escribir el CTRF de la corrida,
el comando termina con error; un reporte anterior no acredita esa ejecución.

Para unir shards usa `npx playwright merge-reports --config reporters/merge.config.ts
<carpeta-de-blobs>`. Esta configuración viene en el scaffold, utiliza el mismo
reporter y conserva los adjuntos de todos los intentos en la entrega consolidada.
Publica `resources/qa/` completo: contiene CTRF, HTML y evidencias, con sus rutas.

## Convención de Id de Caso

Todo título de spec automatizado debe empezar con el id de caso del
runbook, seguido de una etiqueta de prioridad entre corchetes, o de anotaciones `case` y `priority` explícitas:

```typescript
test('TC-01 [critical] - Login con credenciales válidas', async ({ page }) => {
  // ...
});
```

Esto es lo que permite que el CTRF y `.claude/contracts/output/generate-execution-report.mjs`
asocien un video al caso exacto del runbook sin ningún trabajo manual. Una prueba
sin ID o sin prioridad aparece como `UNTRACED-<n>` y añade un error de la corrida.
No permite un GO. Los IDs deben ser únicos por proyecto: un duplicado, incluidas las
repeticiones `--repeat-each`, rechaza la corrida. Para tendencias ejecuta corridas
independientes con runIds nuevos.

## Generar el Reporte Después de una Ejecución

```bash
npx playwright test
node .claude/contracts/output/generate-execution-report.mjs \
  --ctrf resources/qa/reports/<runId>/ctrf.json \
  --expected <casos.json> \
  --out resources/qa/reports/<runId>/execution-report.md
```

Después, adjuntá `resources/qa/reports/<runId>/execution-report.md` y las
rutas de video relevantes (los adjuntos de cada caso en el CTRF) al resumen
final de QA que le entregás al usuario.

## Subida de Artefactos en CI

```yaml
- run: npx playwright test
  env:
    QA_RUN_ID: ${{ github.run_id }}-${{ github.run_attempt }}
- run: node .claude/contracts/output/generate-execution-report.mjs --ctrf resources/qa/reports/${{ github.run_id }}-${{ github.run_attempt }}/ctrf.json --expected resources/qa/plans/casos.json --out resources/qa/reports/${{ github.run_id }}-${{ github.run_attempt }}/execution-report.md --fail-on-no-go
  if: always()
- uses: actions/upload-artifact@v4
  if: always()
  with:
    name: qa-evidence-${{ github.run_id }}-${{ github.run_attempt }}
    path: resources/qa/*/${{ github.run_id }}-${{ github.run_attempt }}
    retention-days: 30
```

El patrón `resources/qa/*/${{ github.run_id }}-${{ github.run_attempt }}` toma la subcarpeta de esa
ejecución dentro de cada carpeta de caso, sin tener que enumerar cada
`TC-xxx` a mano. El artefacto se sube sin el prefijo `resources/qa/`. Para que los enlaces del CTRF
resuelvan, descomprímelo en `resources/qa/` de la raíz del proyecto (por ejemplo,
`actions/download-artifact` con `path: resources/qa`).

Si un proyecto copió `generate-execution-report.mjs` a `scripts/` con una versión
anterior del kit, esa copia busca el renderer en `.claude/skills/ranger/scripts/` y
falla aunque el veredicto sea GO. Reemplaza el paso por
`node .claude/contracts/output/generate-execution-report.mjs`.

Usá `if: always()` en los dos pasos posteriores (generar reporte y subir
artefacto); el reporter organiza la evidencia durante la corrida — no `if: failure()` — ya que la política acá es conservar
la evidencia también de los casos que pasan, y generar/subir el reporte
incluso cuando `playwright test` falló. `--fail-on-no-go` en
`generate-execution-report.mjs` es lo que efectivamente bloquea el pipeline
si el veredicto agregado es `NO-GO`, después de haber escrito igual el
reporte — ver `../../ranger/references/testing_strategies.md#estrategias-de-integración-con-cicd`
para el job completo.

## Almacenamiento y Retención

- El `.webm` de Playwright ya viene comprimido; evitá re-codificarlo salvo
  que algún stakeholder necesite `.mp4` para una herramienta que no pueda
  reproducir `.webm` — si es así, convertí bajo demanda
  (`ffmpeg -i video.webm video.mp4`), no lo hagas por defecto en cada ejecución.
- Ignorá en git toda `resources/qa/` salvo `resources/qa/plans/` y
  `resources/qa/runbooks/`, que sí conviene versionar (son documentos, no
  evidencia binaria):
  ```gitignore
  resources/qa/*
  !resources/qa/plans/
  !resources/qa/runbooks/
  ```
  La evidencia (carpetas por caso, `test-results/`, `playwright-report/`,
  `reports/`) va en almacenamiento de artefactos de CI o un object store,
  no en el repositorio de git.
- Establecé una ventana de retención explícita (ej. `retention-days: 30` en
  CI, o una regla de ciclo de vida si se sube a S3/GCS) — "conservar todo
  para siempre" sin una política de retención crece sin límite.

## Solución de Problemas

| Síntoma | Causa probable | Solución |
|---|---|---|
| No se produce ningún archivo de video | `video` no está configurado, o el contexto se creó antes de aplicar la config | Confirmar `use.video` en la config que gobierna el proyecto en ejecución; verificar que los contextos creados por fixtures también la hereden |
| El video corre tan rápido que no se distingue qué se probó | Falta `slowMo` entre acciones, o el caso no está dividido en pasos | Subir `QA_SLOWMO_MS` (default 300) y envolver los pasos del test en `test.step()` — ver [Legibilidad del Video](#legibilidad-del-video-por-qué-se-ve-acelerado) |
| El video existe pero dura 0 segundos / está corrupto | La prueba crasheó antes de cerrar el contexto | Playwright finaliza el video al cerrar el contexto; asegurate de que el teardown no esté matando el proceso (`process.exit`) a mitad de la prueba |
| El video pesa demasiado en toda la suite | Viewport grande, specs largos, o `video: 'on'` en specs de bajo valor y alto volumen | Fijar `size` en la config; considerar `retain-on-failure` solo para specs de baja prioridad, con el visto bueno del usuario |
| El reporte marca `UNTRACED-<n>` en vez de un ID verificable | Al título de la prueba le falta el prefijo `TC-xxx` o la prioridad | Renombrar el título de la prueba para que empiece con el id de caso y su `[prioridad]` |
| El reporte falla con "Caso/proyecto duplicado en el CTRF" | El mismo id `TC-xxx` se usó en dos títulos de prueba distintos | Corregir el id duplicado en el runbook o en el título del spec |
| El reporte muestra `NO-GO` inesperadamente | Falló un caso etiquetado `[critical]` | Revisar primero el video y `trace.zip` de ese caso (adjuntos en el CTRF) |
| El pipeline de CI sigue en verde aunque el veredicto sea `NO-GO` | Falta `--fail-on-no-go` en el paso de `generate-execution-report.mjs` | Agregar el flag — ver [Subida de Artefactos en CI](#subida-de-artefactos-en-ci) |
| La evidencia de una ejecución anterior desapareció | Se reutilizó el mismo `runId` para dos ejecuciones distintas | Nunca fijes `QA_RUN_ID` manualmente a un valor ya usado; deja que se autogenere con un UUID |
| No queda claro si un caso es flaky o falló una sola vez | No hay ninguna herramienta cruzando corridas históricas | El CTRF marca `flaky` por corrida; para tendencias, comparar CTRF históricos con una herramienta del proyecto (el paquete no incluye un analizador) |

## Varios proyectos e intentos

El CTRF conserva una entrada por caso/proyecto, con los adjuntos del último intento
y `retries` para los anteriores; Playwright deja cada intento en su propia carpeta.
Usa `TC-01 [critical] [HU-123][CA-2] <comportamiento>` o anotaciones `case` y
`priority`. Pasa `--expected <casos.json>` para conservar el alcance previsto. Genera el reporte con el evaluador QA
compartido. `--result <resultado.json>` permite renderizar el resultado contractual.
