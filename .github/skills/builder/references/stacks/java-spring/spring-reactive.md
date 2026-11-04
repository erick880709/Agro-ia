# Programación reactiva (WebFlux, Reactor, Reactive Commons)

Aplica cuando `discover` reporta `stack: reactive` (por ejemplo, el Scaffold con
`reactive=true`, su default). El objetivo es no bloquear, componer de forma
perezosa y propagar errores y cancelación como señales.

## Reglas de firma

- Casos de uso, puertos y adaptadores devuelven `Mono<T>`/`Flux<T>`; nunca
  `Mono<List<T>>` cuando la fuente es naturalmente un flujo, ni `null` dentro de
  un `Mono` (usa `Mono.empty()`).
- Los puertos del dominio usan tipos de Reactor solo si el proyecto ya lo hace
  así en `model` (el Scaffold reactivo sí); no introduzcas Reactor en un dominio
  imperativo.
- Ningún método reactivo debe hacer trabajo antes de la suscripción: envuelve
  efectos con `Mono.defer`, `Mono.fromCallable` o `Mono.fromSupplier`.
  `Mono.just(llamadaCostosa())` ejecuta la llamada aunque nadie se suscriba.

## No bloquear

- Prohibido en código principal: `.block()`, `.blockFirst()`, `.toFuture().get()`,
  `Thread.sleep`, JDBC/JPA, clientes HTTP o SDK síncronos dentro de un flujo.
- Una librería inevitablemente bloqueante se aísla:
  `Mono.fromCallable(() -> sdk.call()).subscribeOn(Schedulers.boundedElastic())`.
  Para AWS usa los `*AsyncClient` con `Mono.fromFuture(() -> client.op(req))`;
  el `Supplier` evita disparar la llamada antes de la suscripción (regla del
  Scaffold).
- `publishOn`/`subscribeOn` solo con propósito claro; no los añadas para
  "arreglar" un bloqueo.
- BlockHound en pruebas si el proyecto lo usa: detecta llamadas bloqueantes en
  hilos no bloqueantes.

## Composición

- `map` para transformaciones síncronas puras; `flatMap` para operaciones
  asíncronas; `concatMap` cuando el orden importa; `flatMap(f, concurrency)` para
  limitar paralelismo contra un tercero.
- `switchIfEmpty(Mono.defer(() -> ...))` o `Mono.error(...)`: sin `defer`, el
  alternativo se construye siempre.
- `Mono.zip`/`Mono.when` para operaciones independientes en paralelo; recuerda
  que `zip` con un `Mono` vacío completa vacío.
- `then`/`thenReturn` para secuenciar efectos; no descartes un `Mono` creado sin
  suscribirlo (un efecto que nunca ocurre).
- No llames `subscribe()` dentro de un flujo (fire-and-forget pierde errores,
  contexto y backpressure); compón y devuelve.
- Idempotencia y check-then-act siguen aplicando: dos `Mono` concurrentes que
  consultan y luego insertan compiten igual que dos hilos.

## Errores

- Errores como señales: `Mono.error(new BusinessException(...))`; no lances
  dentro de un `flatMap` sin envolver.
- `onErrorMap` para traducir excepciones técnicas a las del dominio en el
  adaptador; `onErrorResume` solo con un fallback real y acotado por tipo; no
  conviertas errores en vacío (`onErrorResume(e -> Mono.empty())`) sin regla de
  negocio.
- `timeout(Duration)` en llamadas remotas; `retryWhen(Retry.backoff(n, d)
  .filter(esReintentable))` solo para operaciones idempotentes.
- `doOnError` para registrar sin alterar el flujo; registra una vez, en el límite.

## Contexto y trazas

- Datos transversales (identidad, trace id) viajan en el `Context` de Reactor o
  mediante la propagación automática de Micrometer (Boot 3+ con
  `Hooks.enableAutomaticContextPropagation()` si el proyecto la usa); no uses
  `ThreadLocal`/MDC directamente en flujos reactivos.
- Seguridad: `ReactiveSecurityContextHolder.getContext()`, no
  `SecurityContextHolder`.

## Reactive Commons

- Publicación (`DomainEventBus`/`DirectAsyncGateway`) y escucha
  (`HandlerRegistry`) siguiendo los nombres de eventos, comandos y queries
  existentes; los nombres son contrato con otros servicios.
- Los handlers devuelven `Mono<Void>` y deben ser idempotentes ante
  redistribución; un error en el handler provoca reintento según la
  configuración del broker.

## Pruebas

- `StepVerifier.create(flujo).expectNext(...).verifyComplete()`; para errores,
  `expectErrorMatches`/`expectError(Tipo.class).verify()`. Toda cadena termina en
  un `verify*`: sin él la prueba no se ejecuta.
- `StepVerifier.withVirtualTime` para `delay`, `timeout` e intervalos, sin
  esperas reales.
- Comprueba que un efecto no ocurre antes de la suscripción (pereza) y que la
  cancelación detiene el trabajo cuando el caso lo requiere.
- `WebTestClient` para entry points WebFlux (anotados o Router Functions).
