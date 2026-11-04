# Componentes y reactividad en Angular

## Estructura y ubicación

Sigue el layout existente: por feature (`features/<dominio>`), `core/` para
singletons y `shared/` para piezas reutilizables, librerías Nx con `tags` y
reglas de frontera, o el layout heredado por `NgModule`. No reorganices carpetas
ni conviertas un módulo a standalone dentro de una feature.

- **Standalone** es el default desde v19; en proyectos con NgModules, declara el
  componente nuevo como lo hacen sus vecinos y regístralo en el módulo correcto.
- **Nombres**: respeta la convención observada. Proyectos con sufijos
  (`user-list.component.ts` / `UserListComponent`) los conservan; proyectos
  creados con la guía de estilo v20+ usan nombres por intención sin sufijo
  (`user-list.ts` / `UserList`). Los modelos mantienen `.model.ts`. El selector
  usa el `prefix` del proyecto.
- **Plantillas y estilos**: inline o externos según la convención o la
  instrucción del proyecto.
- **Contenedor y presentación**: los componentes de presentación reciben datos
  por inputs y emiten outputs, sin inyectar servicios de datos. No dividas un
  componente existente solo por aplicar el patrón.
- **Nx**: no importes entre librerías violando `@nx/enforce-module-boundaries`.
  Si el cambio lo exige, es una decisión de frontera (handoff a arquitectura).

## API de componentes

| Necesidad | Moderno (si la versión y el área lo usan) | Heredado aceptable en el área existente |
|---|---|---|
| Entrada | `input()`, `input.required()`, `transform` | `@Input()` |
| Salida | `output()` | `@Output() EventEmitter` |
| Doble enlace | `model()` | `@Input` + `@Output xChange` |
| Consultas | `viewChild()`, `contentChildren()` | `@ViewChild` |
| Host | propiedad `host: {}` en el decorador | `@HostBinding`/`@HostListener` |
| Inyección | `inject()` | constructor |
| Control de flujo | `@if`, `@for (...; track id)`, `@switch`, `@let` | `*ngIf`, `*ngFor` + `trackBy` |
| Carga diferida | `@defer` con `@placeholder`/`@loading` | lazy routes |

- `@for` exige `track`: usa un identificador estable, no `$index` si la lista se
  reordena o filtra. Nunca combines `*ngIf` y `*ngFor` en el mismo elemento.
- Inputs de señal son de solo lectura: no los mutes; deriva con `computed` o
  usa `linkedSignal`/`model` según el caso.
- Etiquetas autocerradas (`<app-x />`) cuando no hay contenido proyectado, si el
  proyecto ya las usa.
- Detección de cambios: en v22 `OnPush` es el valor por defecto y `Default`
  pasa a llamarse `Eager` (el nombre anterior queda deprecado). En versiones
  previas, usa el default del schematic del proyecto. Con `OnPush` o zoneless,
  todo estado que se muestre en la plantilla debe ser una señal, un input o
  pasar por `async`; mutar un campo plano o un objeto en sitio no refresca la vista.

## Señales

- `signal` para estado local; expón `asReadonly()` desde servicios y muta solo
  con métodos del dueño.
- `computed` para estado derivado, siempre puro (sin efectos ni escrituras).
- `linkedSignal` para estado editable que se reinicia cuando cambia una fuente.
- `effect` solo para efectos hacia fuera de Angular (logging, almacenamiento,
  APIs de terceros). No lo uses para copiar una señal en otra: eso es `computed`
  o `linkedSignal`. Para manipular DOM tras render, `afterRenderEffect`/
  `afterNextRender`.
- `untracked` para leer sin crear dependencia dentro de un contexto reactivo.
- Datos asíncronos: `resource`/`rxResource`/`httpResource` son `@experimental`
  hasta v21 y estables desde v22.0 (verificado en los paquetes publicados). En
  versiones previas, usa el patrón del proyecto (servicio + `toSignal`, `async`
  pipe o store).

## RxJS e interoperabilidad

Respeta la convención del proyecto: hay equipos con servicios basados en
Observables, otros con Promises (`firstValueFrom`) y otros con señales. No
mezcles un tercer estilo en una feature.

- Toda suscripción manual tiene dueño y fin: `takeUntilDestroyed()` en contexto
  de inyección (o con `DestroyRef` fuera de él), `toSignal` (se desuscribe al
  destruir su injector) o el pipe `async`. Las llamadas de `HttpClient` terminan
  solas, pero un `subscribe` sobre un `Subject`, `interval`, `valueChanges` o un
  store no.
- No anides `subscribe`: compón con `switchMap` (búsquedas y navegación;
  cancela lo anterior), `concatMap` (orden estricto), `mergeMap` (paralelo
  independiente) o `exhaustMap` (ignorar clics repetidos en un envío).
- `debounceTime` + `distinctUntilChanged` para entrada de usuario; `shareReplay({
  bufferSize: 1, refCount: true })` solo cuando necesitas cachear y entiendes
  su ciclo de vida.
- Maneja errores en el flujo (`catchError`) y conviértelos en un estado de UI;
  un error no capturado completa el Observable y deja la vista sin datos.
- `toSignal` necesita `initialValue` o tipar `undefined`; con `requireSync` solo
  para fuentes síncronas.

## Inyección de dependencias

- `@Injectable({ providedIn: 'root' })` para singletons sin estado por pantalla;
  provee en el componente o en la ruta cuando el estado debe ser por instancia.
- `InjectionToken` para configuración y valores no clase (URLs base, flags); no
  importes `environment.ts` en profundidad de la lógica si el proyecto ya
  inyecta configuración.
- `inject()` solo en contexto de inyección (constructor, inicializadores de
  campo, factorías, guards e interceptores funcionales); fuera de él, NG0203.
- No introduzcas una dependencia circular entre servicios (NG0200); extrae la
  parte compartida.

## Estado de aplicación

Usa el mecanismo existente: servicio con señales, NgRx Store, NgRx Signal Store,
NGXS u otro. No introduzcas una librería de estado ni un nuevo store global para
una feature. En NgRx, sigue su estructura (acciones, reducers, effects,
selectors, `createFeature`) y prueba con sus utilidades.

## Plantillas y rendimiento

- Llamar señales en plantillas es correcto; evita llamadas a métodos que
  calculen o asignen en cada ciclo: usa `computed` o pipes puros.
- `NgOptimizedImage` para imágenes de contenido si el proyecto lo usa.
- `@defer` para bloques pesados no críticos; sus `@placeholder`/`@loading` se
  cargan de forma eager: mantenlos pequeños.
- No reintroduzcas zone.js en una app zoneless ni uses `NgZone.run` como
  parche; en apps con zone.js, `runOutsideAngular` solo para trabajo de alta
  frecuencia que no actualiza la vista.
- Evita barrels (`index.ts`) que arrastren dependencias diferidas al bundle inicial.
