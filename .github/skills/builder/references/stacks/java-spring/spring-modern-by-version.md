# Java y Spring por versión

Usa la forma moderna solo si la release de Java y la versión de Spring Boot
**declaradas en el build** la permiten, y si no contradice la convención del
módulo. No migres código vecino: eso es un `refactor` con su propio encargo.

Fuente: `javac` = verificado compilando con `javac --release 17/21` (JDK 21);
`histórico` = notas de versión conocidas; `comunidad` = skills analizadas
(dr-jskill, spring-boot-testing). Para clases de Spring cuyo paquete dudes,
`spring_toolkit.py class-status <FQN>` contra los jars del proyecto manda sobre
esta tabla.

## Java

| Release | Usa (si el build lo declara) | En lugar de | Fuente |
|---|---|---|---|
| 11 | `var` local, `String.isBlank/strip/lines`, `HttpClient` | Librerías utilitarias equivalentes | histórico |
| 16/17 | `record`, `instanceof` con patrón, `Stream.toList()`, `String.formatted` | POJOs con getters/equals manuales, casts tras `instanceof`, `collect(Collectors.toList())` | javac |
| 17 | `sealed` + `permits`, text blocks, `switch` como expresión | Jerarquías abiertas, concatenación multilínea | histórico |
| 21 | `switch` con patrones y record patterns sobre tipos `sealed` | Cadenas de `instanceof` | javac |
| 21 | `SequencedCollection`: `getFirst()`, `getLast()`, `reversed()` | `list.get(0)`, `list.get(size - 1)`, `Collections.reverse` sobre copia | javac |
| 21 | Virtual threads (`Thread.ofVirtual`, executor por tarea) | Pools grandes para I/O bloqueante (solo si el proyecto los adopta) | javac |
| 21 | `Math.clamp`, `StringBuilder.repeat` | Utilidades propias | javac |
| 22 | Variables sin nombre `_` | Nombres `ignored` | histórico |
| 24 | Stream gatherers; virtual threads sin anclaje en `synchronized` | Colectores ad hoc; `ReentrantLock` solo para evitar anclaje | histórico |
| 25 (LTS) | Scoped values, cuerpos de constructor flexibles, `import module` | `ThreadLocal` para contexto inmutable; fábricas para validar antes de `super` | histórico |

`javac --release N` rechaza tanto la sintaxis como las APIs posteriores a N. Un
JDK local más nuevo no habilita nada que la release declarada no tenga.

## Spring Boot

| Versión | Cambio relevante para código nuevo | Fuente |
|---|---|---|
| 3.0 | Java 17 mínimo; `jakarta.*` en lugar de `javax.*` (persistence, validation, servlet); Spring Framework 6; Security 6 sin `WebSecurityConfigurerAdapter`; `ProblemDetail`; interfaces `@HttpExchange` | histórico |
| 3.1 | `@ServiceConnection` y Testcontainers en desarrollo; soporte Docker Compose | histórico |
| 3.2 | `RestClient`, `JdbcClient`; virtual threads con `spring.threads.virtual.enabled` (Java 21) | histórico |
| 3.4 | `@MockitoBean`/`@MockitoSpyBean` (Framework 6.2) y `@MockBean` deprecado; `MockMvcTester` con AssertJ; logging estructurado (`logging.structured.format.*`) | histórico |
| 4.0 | Spring Framework 7, Jakarta EE 11, Security 7, Hibernate 7; `@MockBean` eliminado | comunidad |
| 4.0 | Jackson 3: clases de API en `tools.jackson.*` (por ejemplo `tools.jackson.databind.ObjectMapper`); las anotaciones siguen en `com.fasterxml.jackson.annotation` | comunidad |
| 4.0 | Starters y autoconfiguración de test modularizados: `@WebMvcTest` pasa a `org.springframework.boot.webmvc.test.autoconfigure` con `spring-boot-starter-webmvc-test` | comunidad |
| 4.0 | `RestTestClient` como alternativa moderna a `TestRestTemplate`; anotaciones de resiliencia y versionado de API en Framework 7 | comunidad |
| — | Testcontainers 2: artefactos `testcontainers-<módulo>` y paquetes por módulo (por ejemplo `org.testcontainers.postgresql.PostgreSQLContainer`) | comunidad |

Las filas `comunidad` provienen de skills que contenían errores internos;
confírmalas con `class-status` o con la documentación de la versión exacta antes
de usarlas.

## Señales de código generado para otra versión

- `javax.persistence`/`javax.validation` en un proyecto Boot 3+, o `jakarta.*`
  en Boot 2.
- `WebSecurityConfigurerAdapter`, `antMatchers` (Security 6 usa
  `requestMatchers`), `authorizeRequests` en lugar de `authorizeHttpRequests`.
- `@MockBean` en specs nuevas con Boot 3.4+; imports de
  `org.springframework.boot.test.autoconfigure.web.servlet.WebMvcTest` en Boot 4.
- `switch` con patrones, `getFirst()` o `reversed()` en un proyecto con release 17.
- `RestTemplate` nuevo donde el proyecto ya usa `RestClient`/`WebClient`.
- `Thread.sleep` o `.block()` en código reactivo.
