# Revisión y diagnóstico en Angular

Complementa [diagnóstico y revisión](../../review-and-debugging.md). La revisión
de cumplimiento va primero; esta lista concreta la revisión de **calidad** del
diff Angular. Clasifica por impacto observable: una preferencia compatible con
el proyecto no bloquea.

## Lista de calidad del diff

**Bloqueante** (defecto probable, seguridad o datos)

- Suscripción manual sin fin (sin `takeUntilDestroyed`, `toSignal`, `async` o
  `unsubscribe`) sobre una fuente que no completa; `subscribe` anidado.
- Estado mostrado en plantilla mutado fuera de señales/inputs en una app
  zoneless o en un componente `OnPush`: la vista no se actualiza.
- `bypassSecurityTrust*` o `[innerHTML]` con datos no confiables; URL de
  `[href]`/`[src]` construida sin validar el esquema; secretos en
  `environment*.ts`.
- Token o credencial enviado a un origen que no es la API propia; comparación de
  origen con `startsWith`/`includes`.
- Guard presentado como control de autorización sin verificación en el backend.
- API `@experimental`/`@developerPreview` introducida sin mandato, o una API
  posterior a la versión instalada; `ng update`, cambio de runner, de zone.js o
  de versiones sin decisión.
- Acceso a `window`/`document`/`localStorage` en código que corre en SSR.
- Presupuesto de bundle elevado para cerrar el cambio.

**Mayor** (mantenibilidad o contrato)

- `effect` usado para sincronizar estado (debería ser `computed` o `linkedSignal`).
- Llamadas HTTP en componentes de presentación, lógica de negocio en plantillas
  o en el componente cuando el área usa servicios o store.
- Estrategia de formulario o de estado distinta a la del área sin decisión;
  una nueva librería añadida para una feature.
- `@for` sin `track` estable (`$index` en listas que cambian de orden).
- Errores HTTP sin estado de UI (la vista queda vacía o colgada).
- Spec que no puede fallar: solo `should create`, aserciones sobre privados,
  `detectChanges` sin esperar en zoneless, `HttpTestingController` sin `verify`.
- Importación entre librerías que rompe fronteras Nx; barrels que arrastran
  código diferido al bundle inicial.
- Controles sin etiqueta accesible, roles ARIA en lugar de elementos nativos,
  patrones de teclado reimplementados cuando el proyecto tiene CDK/Aria.

**Menor** (idioma y estilo, si ESLint o Prettier no lo deciden ya)

- Forma heredada en líneas nuevas donde la versión y el área permiten la
  moderna ([tabla](angular-modern-by-version.md)).
- Nombres o sufijos que no siguen la convención del proyecto; selector sin el
  `prefix`.
- Métodos costosos llamados desde la plantilla.

Antes de reportar, vuelve a leer cada hallazgo contra el diff y elimina los que
no puedas justificar con archivo y línea.

## Diagnóstico dirigido por evidencia

Códigos verificados contra `RuntimeErrorCode` de `@angular/core` 21.2.

| Síntoma o código | Primera observación discriminante |
|---|---|
| La vista no se actualiza | ¿Zoneless u `OnPush`? ¿El valor mostrado es señal/input/`async`? ¿Se mutó un objeto en sitio en vez de crear uno nuevo? |
| NG0100 `ExpressionChangedAfterItHasBeenChecked` | Un valor cambia durante la detección (getter con efectos, escritura en `ngAfterViewInit`, servicio compartido); derivar con `computed` |
| NG0200 dependencia circular | Grafo de `inject()` entre servicios; extraer la parte común |
| NG0201 sin provider | Injector incorrecto (ruta, componente, root), provider faltante en la spec, token no provisto |
| NG0207 provider en contexto equivocado | Un `provideX()` de entorno (p. ej. `provideHttpClient`) declarado en `providers` de un componente; moverlo a `app.config` o a la ruta |
| NG0203 `inject()` fuera de contexto | `inject` en un método o callback; moverlo a un inicializador de campo o usar `runInInjectionContext` |
| NG0500–NG0507 hidratación | HTML de servidor distinto al del cliente (fechas, aleatorios, `window`), DOM manipulado directamente |
| NG0950 input requerido sin valor | Lectura de `input.required()` en el constructor o antes del primer binding; en specs falta `setInput` |
| NG8001 elemento desconocido | Falta el componente en `imports` (standalone) o en el `NgModule` |
| Petición duplicada o fuera de orden | `mergeMap` donde se requería `switchMap`; varias suscripciones a un Observable frío |
| Fuga de memoria | Suscripciones vivas tras destruir: comprobar en la spec con `subject.observed` tras `fixture.destroy()`; Angular DevTools/heap snapshot en ejecución |
| Spec intermitente | Mezcla de `fakeAsync` con zoneless, timers reales, estado compartido entre tests, orden de `TestBed` |
| Error solo en `ng build` | Plantilla validada en AOT (tipos estrictos), presupuesto excedido, import lazy roto |

Herramientas: Angular DevTools (árbol de componentes, profiler, injector),
`ng.getComponent(elemento)` en la consola de una build de desarrollo, mapas de
fuente y el registro de eventos del router (`withDebugTracing()` solo en local).
Antes de culpar a la caché (`.angular/cache`), comprueba que editaste el archivo
compilado, que no hay otra ruta de código con el mismo defecto y que la spec
ejecutada es la tuya (`--include`).

## Entrega a `code-review`

Incluye en el expediente la versión instalada, zoneless o zone.js, el runner,
los comandos ejecutados con su resultado y las specs cubiertas. Esta lista es tu
auto-revisión; el revisor aplica su propio criterio.
