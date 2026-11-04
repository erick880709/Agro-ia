# Angular moderno por versión

Los modelos mezclan APIs de distintas versiones y confunden estados
experimentales con estables. Esta tabla orienta, pero la fuente de verdad es
siempre la versión **instalada**: confirma con
`angular_toolkit.py api-status <símbolo>`, que lee las etiquetas de los `.d.ts`.

## Cómo aplicarla

1. Toma la versión de `node_modules/@angular/core/package.json` (o el rango de
   `package.json`, declarado como supuesto si no hay dependencias instaladas).
2. Solo son elegibles las filas con versión ≤ instalada **y** estado estable en
   esa versión. Las marcadas como experimental o developer preview requieren
   mandato explícito.
3. Aplica la forma moderna en código nuevo o modificado si no contradice la
   convención del área ni las instrucciones del proyecto. No migres archivos
   ajenos: para eso existen los schematics oficiales (`ng generate
   @angular/core:<migración>`) como `refactor` aparte.
4. Si una fila no coincide con lo que reporta `api-status`, manda `api-status`.

Columna **Fuente**: `d.ts` = verificado en los paquetes publicados 20.0.0, 21.2.25 y
22.2.3; `oficial` = skill `angular-developer` (angular/skills, octubre 2026);
`histórico` = notas de versión conocidas, confírmalo en el proyecto.

## Tabla

| Versión | Cambio | Estado | Fuente |
|---|---|---|---|
| 14 | Formularios reactivos tipados; `inject()` en inicializadores de campo | Estable | histórico |
| 15 | Componentes standalone; `provideRouter`; guards/resolvers funcionales; `withInterceptors`; `hostDirectives`; `NgOptimizedImage` | Estable | histórico |
| 16 | `takeUntilDestroyed`/`DestroyRef`; `@Input({ required, transform })`; `withComponentInputBinding` | Estable | histórico |
| 17 | `@if`/`@for`/`@switch` y `@defer` (preview); builder `application` (esbuild) por defecto en apps nuevas; `input()` desde 17.1 (preview) | Preview → estable en 18/19 | histórico |
| 18 | Control flow y `@defer` estables; contenido por defecto en `<ng-content>`; `events` unificado en controles de formulario | Estable | oficial |
| 18 | `provideExperimentalZonelessChangeDetection()` | Experimental | histórico |
| 19 | Standalone por defecto; `@let`; `input()`, `output()`, `model()`, `viewChild()` y consultas de señal estables | Estable (`model`/`output`/`viewChild` `@publicApi 19.0`) | d.ts |
| 19 | `resource()`; `httpResource()` desde 19.2 | Experimental | d.ts |
| 20 | `effect()`, `linkedSignal()` | Estable (`@publicApi 20.0`) | d.ts |
| 20 | Guía de estilo con nombres por intención (sin sufijo `.component`) para proyectos nuevos | Convención | oficial |
| 20.0 | `provideZonelessChangeDetection()` reemplaza al anterior | Developer preview (`@developerPreview 20.0`) | d.ts |
| 20.2 | `provideZonelessChangeDetection()` | Estable (`@publicApi 20.2`) | d.ts |
| 20.2 | Animaciones CSS nativas (`animate.enter`/`animate.leave`) recomendadas sobre `@angular/animations` | Estable | oficial |
| 21 | Apps nuevas zoneless por defecto; Vitest como runner por defecto (`@angular/build:unit-test`); `HttpClient` inyectable sin `provideHttpClient()` | Default de proyectos nuevos | oficial |
| 21 | Signal Forms (`@angular/forms/signals`: `form`, `FormField`, `[formField]`) | **Experimental** (`@experimental 21.0.0`) | d.ts |
| 22 | Signal Forms | Estable (`@publicApi 22.0`) | d.ts |
| 22 | `resource`, `rxResource`, `httpResource` | Estable (`@publicApi 22.0`) | d.ts |
| 22 | `OnPush` por defecto; `ChangeDetectionStrategy.Eager` sustituye a `Default` (deprecado) | Estable | d.ts |
| 22 | `provideClientHydration()` activa hidratación incremental y event replay | Estable | oficial |

## Equivalencias frecuentes

| En lugar de | Usa (si la versión y el área lo permiten) |
|---|---|
| `*ngIf`, `*ngFor` + `trackBy` | `@if`, `@for (x of xs; track x.id)` |
| `@Input() x!: T` | `x = input.required<T>()` |
| `@Output() changed = new EventEmitter<T>()` | `changed = output<T>()` |
| `@ViewChild(Ref) ref!: Ref` | `ref = viewChild.required(Ref)` |
| `constructor(private s: S)` | `private readonly s = inject(S)` |
| `@HostListener('click')` | `host: { '(click)': 'onClick()' }` |
| `ngOnDestroy` + `Subject` + `takeUntil` | `takeUntilDestroyed()` o `toSignal` |
| `subscribe` que asigna un campo para la plantilla | `toSignal(obs$, { initialValue })` o pipe `async` |
| Guard o resolver de clase | `CanActivateFn`/`ResolveFn` |
| Interceptor de clase con `HTTP_INTERCEPTORS` | `HttpInterceptorFn` + `withInterceptors` |
| `HttpClientModule` | `provideHttpClient(...)` (o nada en v21+ si no hay features) |
| `ChangeDetectionStrategy.Default` (v22) | `ChangeDetectionStrategy.Eager` |
| `@angular/animations` en código nuevo (≥ 20.2) | Animaciones CSS nativas |
| `NgModule` para una pieza nueva en app standalone | Componente standalone con `imports` |

## Migraciones oficiales (solo con encargo de refactor)

`ng generate @angular/core:control-flow`, `signal-input-migration`,
`signal-queries-migration`, `output-migration`, `inject`, `self-closing-tag`,
`standalone` (en tres fases, compilando entre cada una). Ejecuta
`ng generate @angular/core: --help` para ver las disponibles en la versión
instalada y acota con `--path`.

## Señales de código generado con una versión equivocada

- Imports de `@angular/forms/experimental` o clases `FormField`/`FormGroup` de
  Signal Forms construidas con `new`: API inexistente.
- `standalone: true` explícito en v19+ (redundante) o ausente en un proyecto
  ≤ v18 que lo requiere.
- `provideExperimentalZonelessChangeDetection` en v20+ (ya no existe: v20.0 lo
  reemplazó por `provideZonelessChangeDetection`, developer preview en 20.0 y
  estable en 20.2).
- `fixture.detectChanges()` como única sincronización en una app zoneless.
- `HttpClientTestingModule` o `RouterTestingModule` en specs nuevas de
  proyectos que ya usan providers.
