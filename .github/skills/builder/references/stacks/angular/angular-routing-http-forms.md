# Rutas, HTTP, formularios, SSR y seguridad en Angular

## Rutas

- Lazy loading con `loadComponent`/`loadChildren` siguiendo cómo lo hace el
  proyecto; no conviertas rutas eager a lazy (ni al revés) fuera del encargo.
- Guards y resolvers funcionales (`CanActivateFn`, `CanMatchFn`, `ResolveFn`)
  con `inject()`; respeta los de clase si el área los usa.
- Un guard es experiencia de usuario, no autorización: el backend debe rechazar
  igualmente. No declares un control de permisos como resuelto solo por un guard.
- Parámetros como inputs (`withComponentInputBinding`) solo si la app ya lo
  activa; si no, `ActivatedRoute` según el patrón existente.
- Añade la ruta nueva al archivo de rutas correcto, con `title` si el proyecto
  lo usa, y comprueba colisiones de path y el orden respecto a comodines (`**`).

## HTTP

- En v21+ `HttpClient` es inyectable sin configuración. `provideHttpClient(...)`
  sigue siendo el lugar para interceptores, XSRF o `withFetch()`; respeta la
  configuración existente y no dupliques providers (un segundo
  `provideHttpClient` en un injector hijo ignora los interceptores del padre
  salvo `withRequestsMadeViaParent()`).
- Interceptores funcionales (`HttpInterceptorFn`) con `withInterceptors`; los de
  clase vía `withInterceptorsFromDi()` si el proyecto ya los usa.
- Credenciales: añade tokens solo a destinos propios comparando el **origen**
  completo (`new URL(url).origin`) o rutas relativas conocidas; un `startsWith`
  sobre la URL base deja pasar `api.dominio.com.atacante.com`.
- Tipa las respuestas (`http.get<Dto>`) y mapea DTO a modelo de dominio en el
  servicio si el proyecto separa ambos; un DTO no es un contrato validado: el
  backend puede enviar otra forma.
- Errores: conviértelos en estado de UI (mensaje, reintento, vacío) sin mostrar
  detalles técnicos; usa el manejador global si existe.
- `httpResource` solo para lecturas reactivas y con la estabilidad que indique la
  versión instalada; las mutaciones (POST/PUT/DELETE) van con `HttpClient`.
- Cancelación: `switchMap` o la cancelación implícita de `toSignal`/`resource`
  al cambiar parámetros; evita respuestas fuera de orden que pisen datos nuevos.

## Formularios

Elige por versión instalada y convención del área, no por moda:

| Situación | Estrategia |
|---|---|
| Formulario existente | Extiende con su misma estrategia (reactivo, template-driven o Signal Forms) |
| Formulario nuevo, v22+, el proyecto ya usa Signal Forms o no tiene convención | Signal Forms (`@angular/forms/signals`, `form()`, directiva `[formField]`) |
| Formulario nuevo en v21 | Reactive Forms tipados: Signal Forms es `@experimental` en v21 |
| Formulario nuevo en ≤ v20 | Reactive Forms tipados (`NonNullableFormBuilder`) o la convención del proyecto |

- Reactive Forms: tipados, `nonNullable`, validadores en el control, `getRawValue()`
  si hay controles deshabilitados, `updateOn` según la UX existente.
- Signal Forms: el modelo es un `signal` con valores iniciales no nulos; no
  combines `[formField]` con `[value]` o `[disabled]` en el mismo input; usa sus
  reglas (`required`, `pattern`, `validate`, `disabled`).
- Template-driven: solo donde el proyecto ya lo usa para formularios simples.
- Controles personalizados: `ControlValueAccessor` (o la interfaz de control de
  Signal Forms en v22+) y pruebas de integración con el formulario.
- La validación del cliente es UX; la del servidor sigue siendo obligatoria.
  Muestra errores accesibles (asociados al control) solo tras interacción si el
  área lo hace así.

## SSR, prerender e hidratación

Si el proyecto tiene `@angular/ssr`:

- No accedas a `window`, `document`, `localStorage` o `navigator` en código que
  corre en servidor; usa `afterNextRender`/`afterRenderEffect`, `DOCUMENT` o
  `isPlatformBrowser`.
- Evita diferencias entre el HTML del servidor y el del cliente (fechas,
  aleatorios, datos por navegador): provocan errores de hidratación (NG0500).
- No añadas SSR ni cambies `outputMode`/rutas de servidor dentro de una feature.

## Seguridad

- Angular sanitiza interpolaciones y `[innerHTML]`; nunca uses
  `bypassSecurityTrust*` con datos de usuario o de API sin una sanitización
  explícita aprobada.
- No construyas URLs de `[href]`/`[src]` con datos no confiables sin validar el esquema.
- Nada secreto en `environment*.ts`, `angular.json` ni el bundle: todo lo que se
  envía al navegador es público.
- Tokens: sigue el mecanismo del proyecto (cookies `HttpOnly` gestionadas por
  backend, almacenamiento en memoria, librería OIDC). No muevas tokens a
  `localStorage` como atajo.
- XSRF: `provideHttpClient` lo configura por defecto para peticiones mutables del
  mismo origen; no lo desactives.

## Accesibilidad e i18n

- HTML semántico primero (`button`, `label`, `nav`); roles ARIA solo cuando no
  hay elemento nativo. Para patrones complejos (listbox, combobox, menu, tabs,
  tree, grid), usa la librería del proyecto (CDK, Material, Angular Aria) en
  lugar de reimplementar teclado y foco.
- Cada control con etiqueta accesible; mensajes de error asociados; foco visible
  y gestionado al abrir diálogos o cambiar de ruta si la app ya lo hace.
- Textos visibles con el mecanismo de i18n existente (`$localize`/`i18n`,
  Transloco, ngx-translate); no hardcodees textos en una app traducida.
