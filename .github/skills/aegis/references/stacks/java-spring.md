# Perfil de seguridad Java / Spring Boot (incluido Scaffold Bancolombia)

Complementa los perfiles de builder (`stacks/java-spring/*`) y la guía
`java-spring-reactive.md` de code-review. Lee primero `pom.xml`/`build.gradle`: la
versión de Spring Boot (y por tanto Spring Security 6.x) y si el stack es imperativo
(MVC) o reactivo (WebFlux) cambian cómo se escribe cada control.

## Tabla de contenido

1. Detección
2. Autenticación y autorización
3. Entrada, persistencia e inyección
4. Serialización y exposición de datos
5. Secretos y configuración
6. Reactivo (WebFlux / Reactor)
7. Scaffold Clean Architecture
8. MCP Server y agentes del Scaffold
9. Recomendaciones de remedio frecuentes

## 1. Detección

- `spring-boot-starter-security`, `spring-boot-starter-oauth2-resource-server`,
  `spring-security-oauth2-jose` → mecanismo de auth.
- `SecurityFilterChain` (MVC) o `SecurityWebFilterChain` (WebFlux); `WebSecurityConfigurerAdapter`
  indica Spring Security < 5.7 (obsoleto): marca como deuda.
- Scaffold: `gradle.properties` con `package=`, módulos `domain/model`, `domain/usecase`,
  `infrastructure/entry-points/*`, `infrastructure/driven-adapters/*`, `applications/app-service`.

## 2. Autenticación y autorización

- **Cadena de filtros:** busca `permitAll()`/`pathMatchers(...).permitAll()` amplios
  (`/**`, `/api/**`), `anyExchange().permitAll()`, `csrf().disable()` en apps con sesión
  de navegador (en APIs stateless con bearer token es aceptable; verifica que no haya
  cookies de sesión).
- **Resource server JWT:** `issuer-uri`/`jwk-set-uri` configurados; validadores de
  `aud` (Spring no valida audiencia por defecto: exige `JwtValidators` +
  `JwtClaimValidator` de `aud` o equivalente). Con Azure External ID/Entra, valida `iss`
  del tenant correcto, `aud` = app ID de la API, `tid` si es multi-tenant y `scp`/`roles`.
- **Autorización por recurso (IDOR/BOLA):** `@PreAuthorize("hasRole")` no protege
  objetos. Busca en handlers/controllers IDs del path que llegan al use case sin el
  principal (`Authentication`, `@AuthenticationPrincipal Jwt jwt`, `ReactiveSecurityContextHolder`).
  El filtro por dueño debe llegar a la consulta (`findByIdAndOwnerId`), no comparar
  después de cargar todo.
- **Method security:** `@EnableMethodSecurity` (o `@EnableReactiveMethodSecurity`)
  presente si se usan `@PreAuthorize`; sin habilitarlo las anotaciones no hacen nada.
- **BFLA:** endpoints administrativos en el mismo router sin regla de rol distinta.

## 3. Entrada, persistencia e inyección

- Bean Validation en la frontera: `@Valid` en el parámetro (MVC); en WebFlux funcional
  (`RouterFunction` del Scaffold) la validación no es automática: busca `Validator`
  explícito o validación en el handler.
- SQL: `@Query(nativeQuery = true)` con concatenación, `EntityManager.createQuery(String +)`,
  `JdbcTemplate` con `String.format`, `DatabaseClient.sql("... " + x)` (R2DBC). Exige
  `:param`/`?`/`.bind()`. Ordenamiento/columnas dinámicas solo desde lista blanca (`Sort`
  validado).
- SpEL: `SpelExpressionParser.parseExpression(input)` → inyección (CWE-917).
- XML: `DocumentBuilderFactory`, `SAXParserFactory`, `XMLInputFactory` sin deshabilitar
  DTD/entidades externas (XXE).
- Archivos: `MultipartFile.getOriginalFilename()` usado en rutas; tamaño máximo
  (`spring.servlet.multipart.max-file-size`, `spring.codec.max-in-memory-size`).
- SSRF: `WebClient.create(urlDelRequest)`, `RestTemplate`/`RestClient` con host de entrada.

## 4. Serialización y exposición de datos

- Jackson `activateDefaultTyping`/`@JsonTypeInfo(use = Id.CLASS)` sobre entrada no
  confiable → deserialización de gadgets (CWE-502).
- Entidades/domain models devueltos directo en la respuesta (API3): exige DTO de salida.
- Lombok `@Data`/`@ToString` en clases con PII o secretos + `log.info("{}", obj)`:
  usa `@ToString.Exclude` o DTOs de log. Revisa `toString()` de `record` con campos sensibles.
- `server.error.include-stacktrace`, `include-message`, `include-binding-errors` en
  `always` fuera de dev; `@ControllerAdvice` que devuelve `e.getMessage()` de excepciones
  de infraestructura.

## 5. Secretos y configuración

- Credenciales en `application.yaml`/`.properties`, `bootstrap.yml`, tests o Dockerfile.
  Si el proyecto ya usa Secrets Manager/Vault (Scaffold: `--secret=true`, adapter
  `secrets`), un secreto literal es `bloqueante` (alineado con code-review).
- Actuator: `management.endpoints.web.exposure.include=*` o `env`, `heapdump`,
  `configprops`, `loggers` expuestos sin auth en perfiles productivos.
- CORS: `allowedOrigins("*")` con `allowCredentials(true)` (Spring lo rechaza en
  versiones recientes, pero `allowedOriginPatterns("*")` lo permite: hallazgo).
- Perfiles: valores inseguros en `application.yaml` base que solo se "corrigen" en un
  perfil que podría no activarse (fail-open por configuración ausente).

## 6. Reactivo (WebFlux / Reactor)

- El contexto de seguridad viaja en el `Context` de Reactor: `SecurityContextHolder`
  (ThreadLocal) en código reactivo devuelve vacío → decisiones de autorización con
  principal nulo. Usa `ReactiveSecurityContextHolder.getContext()`.
- `onErrorResume`/`onErrorReturn` que transforman un error de autorización o de firma
  en éxito o valor por defecto (fail-open, A10).
- Bloqueo (`.block()`, JDBC, SDK síncrono) en el event loop → DoS por agotamiento
  (code-review lo trata en rendimiento; en endpoints públicos es también API4).
- KMS/criptografía: cliente async (`KmsAsyncClient` + `Mono.fromFuture`).

## 7. Scaffold Clean Architecture

- Reglas de dependencia y ArchUnit son obligatorias: un control de seguridad
  implementado en `domain/model` que importa clases de Spring Security viola la
  arquitectura; la autorización de negocio (pertenencia del recurso) vive en el use case
  recibiendo el principal como valor de dominio, y la autenticación en el entry point.
- Driven adapters con `--secret=true` (`DBSecret.java`) y adapter `secrets`
  (`--secrets-backend=aws_secrets_manager|vault`): verifica que no haya fallback a
  credenciales locales en el perfil productivo.
- `entry-points` `reactive-web` con `--authorization=true` habilita JWT: verifica que la
  configuración generada no fue relajada después (`permitAll`, validadores eliminados).
- Mensajería (Reactive Commons, Kafka/Strimzi, SQS): los consumidores son frontera de
  entrada; validar esquema y autenticidad del productor.

## 8. MCP Server y agentes del Scaffold

- `gep --type=mcp` genera seguridad OAuth2/Entra ID con `--enable-security=true` por
  defecto y auditoría (`McpAuditAspect`) con `--enable-audit`. `--enable-security=false`
  o `--enable-audit=false` fuera de desarrollo es hallazgo (alineado con code-review).
- Cada Tool expuesta es una operación invocable por un agente: autorización por tool
  con la identidad del usuario final (no con una cuenta de servicio amplia), validación
  de argumentos, idempotencia y confirmación para efectos irreversibles. Ver
  [IA, agentes y MCP](../ia-agentes-mcp.md).

## 9. Remedios frecuentes (forma, no copia ciega)

```java
// Autorización por recurso en el use case (Scaffold): el principal entra como valor de dominio
public Mono<Movements> list(AccountId accountId, CustomerId requester) {
    return accountGateway.findByIdAndOwner(accountId, requester)
        .switchIfEmpty(Mono.error(new AccessDeniedBusinessException()))
        .flatMap(acc -> movementGateway.findByAccount(acc.id()));
}
```

```java
// Validación de audiencia en resource server
@Bean ReactiveJwtDecoder jwtDecoder(OAuth2ResourceServerProperties p) {
    NimbusReactiveJwtDecoder d = ReactiveJwtDecoders.fromIssuerLocation(p.getJwt().getIssuerUri());
    d.setJwtValidator(new DelegatingOAuth2TokenValidator<>(
        JwtValidators.createDefaultWithIssuer(p.getJwt().getIssuerUri()),
        new JwtClaimValidator<List<String>>("aud", aud -> aud != null && aud.contains(EXPECTED_AUD))));
    return d;
}
```

Test negativo asociado: `WebTestClient` con JWT de otro titular → `403` y verificación de
que el gateway de escritura/evento no fue invocado.
