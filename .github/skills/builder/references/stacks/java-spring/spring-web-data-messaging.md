# Web, datos y mensajería en Spring

## Entry points HTTP

- Sigue el estilo del proyecto: `@RestController` (MVC o WebFlux anotado) o
  Router Functions (`RouterRest` + `Handler`, default del Scaffold con
  `--router=true`). No mezcles estilos en un mismo módulo.
- El entry point traduce: valida la entrada, convierte DTO a comando de dominio,
  invoca el caso de uso y mapea resultado y errores. Sin lógica de negocio ni
  acceso a repositorios.
- Validación con Jakarta Validation (`@Valid` + restricciones en el record de
  entrada). En Router Functions no hay `@Valid` automático: valida con un
  `Validator` inyectado o el helper del proyecto.
- Respuestas: DTO dedicados, nunca entidades JPA. Códigos HTTP coherentes (201
  con `Location` al crear, 204 sin cuerpo, 404/409/422 de negocio según la
  convención existente).
- Errores con un formato estable (`ProblemDetail`/RFC 9457 en Boot 3+ si el
  proyecto no tiene otro) desde `@RestControllerAdvice` o el manejador de
  errores WebFlux, sin trazas, SQL ni mensajes de librerías.
- Versionado y rutas según la convención (`--versioning` del Scaffold, prefijo
  `/api/v1`, cabeceras). Cambiar ruta, verbo, campos, tipos u obligatoriedad es
  cambio de contrato (aplica [contratos y datos](../../contracts-and-data.md)).
- Paginación acotada: límite máximo del lado servidor; no devuelvas colecciones
  sin límite.

## Persistencia con JPA

- `FetchType.LAZY` en asociaciones (`@ManyToOne` es EAGER por defecto: decláralo
  LAZY). Carga lo necesario por caso de uso con `JOIN FETCH`, `@EntityGraph` o
  proyecciones DTO; vigila N+1 activando el log de SQL o el contador de
  sentencias en la prueba.
- `spring.jpa.open-in-view=false` es lo deseable; si el proyecto lo tiene en
  `true`, no lo cambies en una feature, pero no dependas de él para cargas
  perezosas en la vista.
- `BigDecimal` con `precision` y `scale` en `@Column`; enums con
  `EnumType.STRING`; `equals/hashCode` de entidades basados en id estable, no en
  todos los campos.
- Consultas con parámetros enlazados (`:param`, Criteria, Specifications).
  Nunca concatenación de entrada en JPQL/SQL nativo.
- Esquema mediante la herramienta del proyecto (Flyway/Liquibase); `ddl-auto`
  distinto de `validate`/`none` en entornos compartidos es un hallazgo.
- Operaciones masivas: paginación o streaming con `@QueryHints` de fetch size;
  no cargues tablas completas en memoria.

## Transacciones

- `@Transactional` en el límite de la operación de negocio que lo requiere,
  normalmente el adaptador o un servicio de aplicación; en el Scaffold, no en
  `usecase` (dominio sin Spring). Si el caso de uso necesita atomicidad entre
  varios puertos, coordínalo con un puerto transaccional o un adaptador que
  agrupe la operación, y regístralo como decisión de diseño.
- Trampas que invalidan `@Transactional` de forma silenciosa:
  - auto-invocación (`this.metodo()` no pasa por el proxy);
  - métodos `private` o `final`;
  - excepciones checked, que no hacen rollback salvo `rollbackFor`;
  - capturar la excepción dentro del método transaccional.
- `readOnly = true` en lecturas cuando el proyecto lo usa; transacciones cortas,
  sin llamadas HTTP remotas dentro.
- Efectos externos tras confirmar: `@TransactionalEventListener(phase =
  AFTER_COMMIT)` o patrón outbox si el proyecto lo tiene; publicar a un broker
  dentro de la transacción y luego hacer rollback deja eventos huérfanos.
- R2DBC/reactivo: `TransactionalOperator` o `@Transactional` reactivo; la
  transacción vive en el contexto de Reactor, no en el hilo.

## Mensajería y consumidores

- Idempotencia en el límite que la garantiza: restricción única, inserción
  atómica (`markIfAbsent`/`INSERT ... ON CONFLICT`), versión optimista. Un
  `exists()` seguido de `save()` es una carrera bajo redistribución concurrente.
- Si el procesamiento falla tras marcar el mensaje, libera la marca o usa un
  estado que permita el reproceso; la confirmación (ack) se hace después del
  efecto, no antes.
- Reintentos con backoff y límite, DLQ según la plataforma; distingue errores
  reintentables (técnicos) de no reintentables (validación, negocio).
- Reactive Commons (Scaffold `asynceventbus`/`asynceventhandler`): sigue sus
  nombres de evento, comando y query y el modo EDA configurado; un cambio de
  nombre o de esquema de evento es cambio de contrato con consumidores.
- Kafka/IBM MQ/SQS: respeta grupo, partición/clave, orden y confirmación
  configurados; no cambies `enable.auto.commit`, `ack-mode` ni concurrencia
  como efecto colateral.

## Clientes HTTP y resiliencia

- Usa el cliente del proyecto (`RestClient` o `@HttpExchange` en Boot 3.2+,
  `WebClient` en reactivo, `RestTemplate` heredado, adaptador `restconsumer`
  del Scaffold). Timeouts de conexión y lectura explícitos; nunca un cliente sin
  límite contra un tercero.
- Resiliencia con el mecanismo existente (Resilience4j, anotaciones de
  resiliencia de Spring Framework 7 en Boot 4, operadores de Reactor). Reintenta
  solo operaciones idempotentes y con backoff; circuit breaker y bulkhead según
  la convención del servicio.
- Traduce errores del tercero a errores técnicos del dominio; no propagues
  cuerpos de respuesta externos al cliente.

## Seguridad

- Configuración con `SecurityFilterChain` (o `SecurityWebFilterChain` en
  WebFlux) como bean; nunca `WebSecurityConfigurerAdapter` (eliminado en
  Security 6).
- Autorización explícita para cada ruta nueva (`authorizeHttpRequests`/
  `authorizeExchange` o `@PreAuthorize` si el proyecto usa seguridad de
  métodos); denegar por defecto. Verifica la pertenencia del recurso al usuario
  autenticado, no solo el rol (IDOR).
- Resource server JWT: valida emisor, audiencia y expiración según la
  configuración existente; no decodifiques tokens a mano.
- CSRF solo se desactiva en APIs sin estado con autenticación por token; no lo
  desactives en aplicaciones con sesión.
- Contraseñas con `PasswordEncoder` (`DelegatingPasswordEncoder`/BCrypt);
  secretos fuera del repositorio; nada de PII, tokens ni números de cuenta en
  logs.

## Observabilidad

- SLF4J con mensajes parametrizados (`log.info("x={}", x)`); nivel según la
  convención; un error se registra una vez, en el límite.
- Logging estructurado (Boot 3.4+ `logging.structured.format.*`, o el appender
  del proyecto) y correlación por trazas (Micrometer Tracing) si existen; no
  inventes un MDC paralelo.
- Métricas con `MeterRegistry`/`@Observed` siguiendo los nombres existentes;
  etiquetas de baja cardinalidad (nunca ids de usuario).
- Actuator: no expongas endpoints sensibles (`env`, `heapdump`, `beans`) sin la
  configuración de seguridad existente.
