# Java, Spring Boot y Reactor

Complementa los ejes generales con fallos frecuentes del stack Java/Spring.
Si el proyecto usa otro lenguaje, aplica los principios equivalentes; no
fuerces patrones de Java.

## Lenguaje (17/21+)

- `record` para valores inmutables de transporte; no para entidades JPA.
- `Optional` solo como retorno; nunca campo ni parámetro; evita `isPresent()` +
  `get()` (usa `map/orElse/orElseThrow`). `Optional.get()` sin guarda es bug.
- `switch` de expresión exhaustivo sobre enums/sealed; `default` que oculte un
  caso nuevo es riesgo.
- `equals/hashCode` coherentes; `BigDecimal.equals` compara escala (usa
  `compareTo`); dinero nunca en `double`/`float`.
- Fechas: `java.time` con zona explícita (`ZoneId`), nunca `new Date()` para
  lógica de negocio; `LocalDateTime.now()` sin `Clock` inyectado complica tests.
- Streams: no para efectos secundarios simples; no `parallelStream` en código de
  servidor sin medir; colecciones mutables devueltas desde getters.
- Excepciones: no capturar `Exception`/`Throwable` genérico salvo en el borde;
  no `e.printStackTrace()`; conservar la causa al envolver.

## Spring

- Inyección por constructor con campos `final` (`@RequiredArgsConstructor`);
  `@Autowired` en campo es `menor` en general y `bloqueante` en el scaffold.
- `@Value` en campo → parámetro del constructor (Rule_2.7). Mejor aún,
  `@ConfigurationProperties` validadas para grupos de propiedades.
- `@Transactional`: en métodos públicos llamados desde fuera del bean; cuidado
  con auto-invocación, `readOnly` en consultas, propagación explícita en
  operaciones anidadas. En WebFlux usa transacciones reactivas
  (`TransactionalOperator`/R2DBC), no JPA.
- Validación: `@Valid` en el parámetro del controller y constraints en el DTO;
  sin `@Valid`, las anotaciones del DTO no se ejecutan.
- Manejo de errores centralizado (`@ControllerAdvice` o handler funcional en
  WebFlux) con respuestas consistentes, sin stack trace al cliente.
- Configuración por perfil sin secretos; `application-local` no debe llegar a
  producción.
- Lombok: `@Data` en entidades JPA (equals/hashCode con relaciones perezosas,
  `toString` recursivo y con PII); prefiere `@Getter` + `@Builder` explícitos.
  `@Builder` sin `toBuilder` cuando se necesita copia.

## JPA (proyectos imperativos)

- N+1 por relaciones `LAZY` recorridas en bucle; `EAGER` por defecto en
  `@ManyToOne` arrastra datos. Usa `JOIN FETCH`/`@EntityGraph` puntuales.
- `open-in-view` habilitado oculta N+1 en la capa web.
- Bloqueo optimista (`@Version`) para entidades con actualización concurrente.
- Consultas nativas con concatenación → inyección.
- Migraciones (Flyway/Liquibase): incremental, no editar las ya aplicadas,
  nulabilidad y backfill con datos existentes, índices para filtros nuevos.

## Reactor / WebFlux

Ver [rendimiento y concurrencia](performance-and-concurrency.md) §Reactivo. Además:

- Tests con `StepVerifier` (`expectNext`, `expectError`, `verifyComplete`); un
  test que construye el `Mono` y no lo verifica pasa sin ejecutar nada.
- `Mono<Void>` encadenado con `then()` correctamente; `map` que devuelve un
  `Mono` (debería ser `flatMap`) produce `Mono<Mono<T>>` silencioso.
- `switchIfEmpty(Mono.error(...))` construye el error eagerly: usa
  `Mono.defer` si construir el error es costoso o tiene efectos.
- `Flux.collectList()` sobre flujos sin límite carga todo en memoria.
- `WebClient`: `retrieve()` con `onStatus` para errores, timeouts
  (`responseTimeout`, `timeout()`), reintentos con `Retry.backoff` y tope.
- Contexto: usar `contextWrite`/`deferContextual` para propagación (trazas,
  usuario); no `ThreadLocal`.

## Mensajería (Reactive Commons, Kafka, MQ, SQS)

- Idempotencia del consumidor ante redelivery; clave estable por mensaje.
- Ack/commit después del efecto, no antes; manejo de mensajes envenenados
  (DLQ, reintentos limitados).
- Esquema/versión del evento: campo nuevo obligatorio rompe consumidores
  existentes; renombres son incompatibles.
- No loguear payloads con PII.
