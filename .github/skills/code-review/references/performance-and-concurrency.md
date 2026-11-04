# Rendimiento y concurrencia

Reporta rendimiento solo cuando el impacto es plausible a la escala real del
flujo. Cuantifica: "N+1 en un listado paginado de 50 = 51 consultas" convence;
"podría ser lento" no.

## Acceso a datos

- **N+1:** consulta o llamada remota dentro de un bucle/`flatMap` por elemento.
  Remedio: carga en lote (`IN`, `findAllById`, `JOIN FETCH`, `@EntityGraph`,
  DataLoader en GraphQL).
- Listados sin paginación ni límite; `findAll()` en tablas de negocio.
- Consultas sobre columnas sin índice en filtros nuevos (revisa la migración).
- Transacciones largas que incluyen llamadas remotas; `@Transactional` en
  métodos privados o llamados desde la misma clase (no aplica el proxy).
- Cargar entidades completas para leer un campo.

## Recursos

- Streams, conexiones, clientes HTTP o `ExecutorService` sin cerrar; crear un
  cliente (WebClient, SDK de AWS, `ObjectMapper`) por petición en vez de
  reutilizar un bean.
- Caches sin límite ni expiración; colecciones estáticas que crecen.
- Timeouts ausentes en llamadas salientes; reintentos sin backoff ni tope.

## Reactivo (WebFlux / Reactor)

En proyectos `reactive=true` estos son casi siempre `bloqueante` o `mayor`:

- `.block()`, `.blockFirst()`, `.toFuture().get()`, `Thread.sleep` en código de
  producción: bloquea el event loop.
- Drivers o SDK síncronos (JDBC/JPA, `S3Client`, `KmsClient`, `DynamoDbClient`)
  en flujo reactivo sin `subscribeOn(Schedulers.boundedElastic())`; el scaffold
  exige clientes AWS `*AsyncClient` con `Mono.fromFuture` (Rule_1.5).
- `subscribe()` dentro de un operador (fire-and-forget que pierde errores y
  contexto); resultado de un `Mono` ignorado (nunca se ejecuta).
- `Mono.just(llamadaCostosa())`: ejecuta eagerly; usa `Mono.fromCallable`/`defer`.
- `flatMap` sin límite de concurrencia sobre listas grandes hacia un servicio
  externo; considera `flatMap(f, n)` o `concatMap`.
- Errores manejados con `try/catch` alrededor del pipeline en vez de
  `onErrorResume`/`onErrorMap`; `onErrorResume(e -> Mono.empty())` que oculta
  fallos.
- Estado mutable compartido entre señales; `ThreadLocal`/MDC sin propagación de
  contexto.

## Concurrencia (imperativo)

- Check-then-act sin atomicidad (verificar saldo y luego debitar en dos pasos).
  Remedio: operación atómica en BD (`UPDATE … WHERE saldo >= :monto`), bloqueo
  optimista (`@Version`) o constraint único.
- Idempotencia: consumidores de colas/eventos que aplican el efecto dos veces
  ante redelivery. Busca clave de idempotencia persistida y no regenerada por
  intento.
- Campos mutables en beans singleton (en el scaffold, Rule_2.5/2.7 exigen
  `final`); `SimpleDateFormat` compartido; `HashMap` concurrente.
- Virtual threads con `synchronized` sobre I/O (pinning) en Java 21.

## Hot paths

- Regex compiladas por llamada, concatenación en bucles, serialización repetida,
  logs con formateo costoso sin guardar el nivel.
- Optimización prematura: no pidas micro-optimizaciones en código frío; es `nit`.
