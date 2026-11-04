# Reglas del Scaffold Clean Architecture (Bancolombia)

Aplica cuando el repositorio fue generado con el plugin
`co.com.bancolombia.cleanArchitecture`. Señales: `main.gradle`,
`gradle.properties` con `package=` y `reactive=`, módulos `domain/model`,
`domain/usecase`, `infrastructure/{entry-points,driven-adapters,helpers}`,
`applications/app-service`, y un `ArchitectureTest` en app-service.

Estas reglas son obligatorias en ese tipo de proyecto: su violación es
`bloqueante` (dependencias entre módulos, nombres prohibidos que harán fallar
ArchUnit) o `mayor` (patrones que el plugin desaconseja). Si el proyecto
desactivó una regla por configuración documentada, respétalo y repórtalo como
`fyi`; si la desactivó **en este cambio**, es `mayor`.

## 1. Regla de dependencias entre módulos

```
app-service ──► entry-points, driven-adapters, helpers, usecase, model
entry-points / driven-adapters / helpers ──► usecase y/o model
usecase ──► model (únicamente)
model ──► (nada)
infraestructura ──X──► app-service
```

Revisa los `build.gradle` de cada módulo tocado (`implementation project(':x')`)
y los imports Java. Un import de `co.com.<pkg>.<adapter>` desde `usecase` o
`model` es violación aunque Gradle no lo detecte (p. ej. por clase duplicada).

- `model` sin dependencias. Excepción: BOMs listados en
  `cleanPlugin { modelProps { whitelistedDependencies = "…" } }`.
- Los puertos (gateways) son interfaces en `model/.../gateways`; sus
  implementaciones viven en `driven-adapters`. Un use case que instancia un
  adapter o usa `WebClient`/`JdbcTemplate`/SDK directamente rompe la regla.
- Solo `app-service` tiene `main`. El ensamblaje de beans de use cases lo hace
  app-service; no anotes use cases con `@Service`/`@Component` si el proyecto
  usa el registro automático del scaffold.
- Verificación autoritativa: `./gradlew validateStructure` (`vs`) y el
  `ArchitectureTest`. `scripts/scaffold_check.py` es un pre-chequeo heurístico.

## 2. Reglas ArchUnit

| Regla | Qué verificar | Severidad típica |
|---|---|---|
| Rule_2.2 | Clases de dominio (model/usecase) sin sufijos `dto`, `request`, `response` (insensible a mayúsculas; lista en `arch.unit.forbiddenDomainSuffixes`) | bloqueante |
| Rule_2.4 | Clases de dominio sin nombres de tecnología: `rabbit, sqs, sns, ibm, dynamo, aws, mysql, postgres, redis, mongo, rsocket, r2dbc, http, kms, s3, graphql, kafka` (lista en `arch.unit.forbiddenDomainClassNames`) | bloqueante |
| Rule_2.7 (campos) | Campos de modelos/use cases sin esos nombres de tecnología | bloqueante |
| Rule_2.5 | Use cases solo con atributos `final` (sin estado mutable) | bloqueante |
| Rule_2.7 (beans) | Beans con atributos `final` e inyección por constructor; `@Value` solo como parámetro del constructor | bloqueante |
| Rule_1.5 | En reactivo, clientes AWS `*AsyncClient` con `Mono.fromFuture` | mayor/bloqueante |

`arch.unit.skip=true` en `gradle.properties` desactiva todo: si el cambio lo
introduce, `bloqueante`.

Ejemplos de corrección: `DynamoUserGateway` → `UserGateway`;
`UserRequest` en model → `User`; `private String rabbitContentType` →
`contentType`; `@Value` en campo → parámetro del constructor con campo `final`.

## 3. Reactivo vs imperativo

`reactive=true` en `gradle.properties` o `--type=reactive`:

- Gateways y use cases devuelven `Mono`/`Flux`; no `.block()` en producción.
- Adapters con drivers reactivos (`r2dbc`, `mongodb` reactivo, `webflux`
  `restconsumer`). JPA en un proyecto reactivo es `mayor` salvo aislamiento en
  `boundedElastic` justificado.
- Ver [rendimiento y concurrencia](performance-and-concurrency.md) §Reactivo.

Imperativo (`restmvc`): no mezclar tipos Reactor sin necesidad.

## 4. Módulos generados y tareas del plugin

- Un módulo nuevo debería venir de `gda`/`gep`/`gh`/`gm`/`guc` (o seguir su
  estructura). Estructura manual divergente es `menor` si funciona, `mayor` si
  rompe `vs`.
- Cambios en `main.gradle`, `build.gradle` raíz o `gradle.properties` que
  coincidan con lo que `ca` o `u` (updateCleanArchitecture) regeneran: verifica
  que no se perdieron personalizaciones del proyecto.
- Un upgrade del plugin (`u`) es un cambio de dependencias: revisa changelog,
  versiones de Spring Boot/Lombok/Gradle arrastradas y suite verde.
- Contract-first (`--from-swagger`): el contrato es la fuente; editar el código
  generado en vez del YAML es `mayor`.

## 5. Consistencia de nombres y paquetes

- Paquete base del `gradle.properties` (`package=`) respetado en módulos nuevos.
- Modelos de entrada/salida de API (DTO, Request, Response) viven en el
  entry-point, mapeados al modelo de dominio; nunca expuestos desde `model`.
- Modelos de persistencia (entities JPA, `@Table`) en el driven adapter, con
  mapper al dominio; anotaciones de persistencia en `model` son `bloqueante`.

## 6. Pruebas en el scaffold

- `ArchitectureTest` no debe modificarse para relajar reglas.
- Tests de use case con mocks de gateways y `StepVerifier` en reactivo.
- `gat` (acceptance, Karate) y `gpt` (JMeter) existen como módulos aparte: si el
  cambio altera un contrato y hay acceptance tests, deben actualizarse.
