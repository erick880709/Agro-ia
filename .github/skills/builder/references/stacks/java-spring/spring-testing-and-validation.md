# Pruebas y validación Java / Spring

## Comandos

Usa el wrapper y las tareas del proyecto. `spring_toolkit.py validate` las
ejecuta en orden, solo con `gradlew`/`mvnw`, y reporta `not_run` si faltan
artefactos o red.

| Paso | Gradle (wrapper) | Maven (wrapper) | Cuándo |
|---|---|---|---|
| Compilación | `./gradlew :mod:compileJava :mod:compileTestJava` | `./mvnw -pl mod -am -DskipTests test-compile` | Siempre |
| Tests focalizados | `./gradlew :mod:test --tests '*BlockCardUseCaseTest'` | `./mvnw -pl mod -am test -Dtest=BlockCardUseCaseTest -Dsurefire.failIfNoSpecifiedTests=false` | Por incremento |
| Analizadores | `checkstyleMain`, `pmdMain`, `spotlessCheck`, `spotbugsMain` si están configurados | `checkstyle:check`, `spotless:check`, `pmd:check` | Si existen; no los añadas |
| Arquitectura | `./gradlew validateStructure` (Scaffold) y `ArchitectureTest`/ArchUnit | Pruebas ArchUnit | Si cambian módulos, dependencias o paquetes |
| Build completo | `./gradlew build` | `./mvnw verify` | Al cerrar o si cambian contratos, módulos o configuración |
| Cobertura y mutación | `jacocoTestReport`, `pitest` | `jacoco:report`, `pitest` | Solo si el proyecto los usa; un porcentaje no es criterio de aceptación |

Un filtro de tests que no ejecuta ninguna prueba es un fallo de evidencia, no un
éxito.

## Elegir el nivel de prueba

| Qué demuestras | Herramienta |
|---|---|
| Regla de negocio en caso de uso / dominio | JUnit 5 sin Spring; fakes o mocks de los puertos |
| Flujo reactivo | `StepVerifier` (ver [programación reactiva](spring-reactive.md)) |
| Contrato HTTP MVC | `@WebMvcTest` + `MockMvc` o `MockMvcTester` (Boot 3.4+) |
| Contrato HTTP WebFlux | `@WebFluxTest` o `WebTestClient` con el router/handler |
| Consultas JPA y mapeos | `@DataJpaTest` con la base real del proyecto vía Testcontainers si existe; H2 no demuestra compatibilidad con Oracle/PostgreSQL |
| Cliente HTTP saliente | `@RestClientTest`/`MockRestServiceServer`, WireMock o MockWebServer según el proyecto |
| JSON | `@JsonTest` si la serialización es contrato |
| Cableado completo | `@SpringBootTest` mínimo; reutiliza el contexto cacheado |
| Dependencias de arquitectura | ArchUnit / `validateStructure` |

- Dobles: `@MockitoBean`/`@MockitoSpyBean` en Boot 3.4+ (`@MockBean` está
  deprecado en 3.4 y eliminado en 4.0); Mockito puro fuera de Spring. Prefiere
  fakes de los puertos en el dominio cuando el comportamiento importa más que
  la interacción.
- Aserciones sobre el resultado observable y el estado de los puertos (lo que se
  guardó, lo que se publicó), no sobre la secuencia interna de llamadas, salvo
  que la interacción sea el requisito (por ejemplo, "no audita si ya estaba
  bloqueada").
- Dinero: `assertEquals(new BigDecimal("0.12"), resultado)` exige también la
  escala; usa `compareTo` cuando la escala no sea parte del requisito.
- Concurrencia e idempotencia: lanza N tareas simultáneas con un `CountDownLatch`
  de salida y verifica que el efecto ocurre una vez; repite varias rondas. Un
  test secuencial de duplicados no detecta carreras.
- Tiempo: `Clock` inyectado o tiempo virtual; sin `Thread.sleep` como
  sincronización.
- Testcontainers solo si el proyecto ya lo usa y el entorno tiene Docker; si no,
  la integración real queda `not_run` y se declara.
- Una prueba generada vacía, con `assertTrue(true)` o que solo comprueba que el
  contexto arranca no es evidencia de comportamiento.

## Comprobar que la prueba puede fallar

Para un bug, la prueba nueva falla en la versión inicial por la aserción del
defecto. Para lógica crítica, aplica una mutación controlada en un workspace
aislado y confirma que la prueba la detecta. Ejemplos: cambiar `HALF_EVEN` por
`HALF_UP`, sustituir `markIfAbsent` por `exists` + `save` o quitar la liberación
tras un fallo. Revierte la mutación después.

## Contexto de la evidencia

Registra JDK y release de compilación, versión de Spring Boot, wrapper y versión
de Gradle/Maven, módulos y filtros ejecutados, base de datos o broker reales
frente a dobles, y la revisión validada. Distingue fallos preexistentes,
regresiones y falta de entorno (repositorio de artefactos, Docker, credenciales).
