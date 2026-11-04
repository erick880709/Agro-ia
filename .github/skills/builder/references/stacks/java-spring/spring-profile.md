# Perfil Java / Spring Boot

Capa específica de stack para Builder. Concreta el flujo de `SKILL.md` cuando el
componente afectado es Java (con o sin Spring Boot); no reemplaza sus invariantes.
Las convenciones observadas del proyecto y el mandato del usuario prevalecen
sobre cualquier preferencia de esta guía.

## Activación

Aplica el perfil a cada proyecto con `pom.xml`, `build.gradle(.kts)` o
`settings.gradle(.kts)` afectado por el cambio. Ejecuta primero el descubrimiento
estático (no compila ni descarga nada):

```text
python <skill-root>/scripts/spring_toolkit.py discover <ruta>
```

Devuelve: herramienta de build y wrapper, release de Java, versión de Spring Boot,
si es un proyecto del **Scaffold Clean Architecture de Bancolombia** y sus
propiedades (`package`, `reactive`, `lombok`), stack **imperativo o reactivo**,
módulos, librerías (JPA, R2DBC, Reactive Commons, Lombok, MapStruct,
Testcontainers, ArchUnit, analizadores estáticos), archivos de instrucciones para
agentes y un recuento de patrones (inyección por campo, `javax` frente a
`jakarta`, `.block()` en código principal, `@MockBean` frente a `@MockitoBean`).

## Orden de autoridad

1. Mandato del usuario y fuentes del cambio.
2. Si `discover` reporta `bancolombia_scaffold: true`, la
   [referencia del Scaffold](../../scaffold-clean-architecture.md) manda sobre la
   **estructura**: capas, módulos, regla de dependencias, nombres y tareas
   (`gm`, `guc`, `gda`, `gep`, `vs`). Este perfil aporta las prácticas de
   **código** dentro de esa estructura y nunca la contradice.
3. Archivos de instrucciones para agentes (incluidos los anidados), reglas de
   Checkstyle/PMD/Spotless/ArchUnit y `ArchitectureTest` del proyecto.
4. Convención dominante del módulo de referencia (Lombok o no, MapStruct o mapeo
   manual, records, estilo de errores, nombres de pruebas).
5. Esta guía.

## Versiones objetivo

- **Java**: la release declarada en el build (`toolchain.languageVersion`,
  `sourceCompatibility`, `maven.compiler.release`, `java.version`, o
  `javaVersion` en `gradle.properties` del Scaffold) define el lenguaje y la API
  utilizables, no el JDK local. `javac --release N` rechaza APIs posteriores; el
  JDK local más nuevo no las habilita.
- **Spring Boot**: la versión del plugin o del parent. Los paquetes y
  anotaciones cambian entre mayores (Boot 3 → 4: Jackson 3, módulos de
  autoconfiguración de test, Testcontainers 2). Antes de importar una clase cuyo
  paquete dudes, verifica con:

  ```text
  python <skill-root>/scripts/spring_toolkit.py class-status <FQN>...
  ```

  que busca la clase en los jars ya presentes en las cachés locales de Maven y
  Gradle e indica si `javap` la marca `@Deprecated`. Si el jar no está en caché,
  la ausencia no es concluyente: decláralo.
- No subas Java, Spring Boot, el plugin del Scaffold (`./gradlew u`) ni
  dependencias gestionadas dentro de una feature. Es una decisión con dueño.

Consulta [Java y Spring por versión](spring-modern-by-version.md).

## Imperativo o reactivo

El stack lo fija el proyecto (`reactive=true` en el Scaffold, `webflux` frente a
`web`/`webmvc`). No mezcles modelos en un mismo flujo: nada de `.block()` en un
flujo reactivo ni de `Mono`/`Flux` como fachada de código bloqueante. Si el
cambio exige integrar una librería bloqueante en un servicio reactivo, aíslala
según [programación reactiva](spring-reactive.md).

## Mapa de lectura por tipo de cambio

| Necesidad del cambio | Guía |
|---|---|
| Ubicación, DI, records, Lombok/MapStruct, errores de dominio, configuración | [Diseño e idiomas](spring-design-and-idioms.md) |
| Endpoints, validación, errores HTTP, JPA/R2DBC, transacciones, mensajería, clientes HTTP, seguridad, observabilidad | [Web, datos y mensajería](spring-web-data-messaging.md) |
| Proyectos WebFlux/Reactor y Reactive Commons | [Programación reactiva](spring-reactive.md) |
| Pruebas, comandos, evidencia | [Pruebas y validación](spring-testing-and-validation.md) |
| Elegir API según Java/Spring Boot declarados | [Java y Spring por versión](spring-modern-by-version.md) |
| Revisión de calidad y diagnóstico | [Revisión y diagnóstico](spring-review-and-debugging.md) |

## Superposición sobre el flujo de Builder

| Paso de Builder | Qué añade el perfil |
|---|---|
| 1. Descubrir | `discover`; leer el módulo de referencia, su test y la configuración (`application*.yaml`, perfiles); en Scaffold, ubicar el puerto (`model/.../gateways`), el adaptador y el ensamblaje en `app-service` |
| 2. Especificar | Declarar Java/Boot objetivos, stack imperativo o reactivo, contratos públicos (rutas, DTO, eventos, esquema) y semántica transaccional o de entrega |
| 3. Diseñar | En Scaffold: modelo y puerto en `model`, lógica en `usecase`, tecnología en `driven-adapters`/`entry-points`; fuera del Scaffold, el empaquetado del proyecto |
| 4. Implementar | Generar con la tarea del Scaffold si el proyecto lo hace así (`gm`, `guc`, `gda`, `gep`) y revisar lo generado; inyección por constructor, campos `final` |
| 5. Validar | Escalera: compilación → tests focalizados → analizadores configurados → `validateStructure`/ArchUnit → build completo cuando cambian contratos o módulos |
| 6. Entregar | JDK, release, Boot, wrapper, módulos y tests ejecutados; qué se verificó contra infraestructura real y qué con dobles |

## Uso de herramientas

- Usa el wrapper del proyecto (`./gradlew`, `./mvnw`). No uses Gradle/Maven
  globales ni otra versión: los plugins y el Scaffold dependen de la del wrapper.
- No ejecutes `./gradlew ca` sobre un proyecto existente (sobrescribe
  `main.gradle`, `build.gradle` y `gradle.properties`) ni `./gradlew u` sin
  commit previo y mandato.
- Si el entorno no tiene acceso al repositorio de artefactos, la compilación
  queda `not_run` con esa razón. No sustituyas dependencias ni versiones para
  poder compilar.

## Límites del perfil

- No crea microservicios, módulos de infraestructura nuevos con tecnología no
  usada aún, pipelines, Dockerfiles ni manifiestos de despliegue: eso es
  baseline, arquitectura o el flujo operacional.
- No introduce Lombok, MapStruct, una librería de resiliencia, de mensajería o
  de mapeo que el proyecto no use.
- Las migraciones de esquema siguen [contratos y datos](../../contracts-and-data.md).

## Fuentes destiladas

Síntesis adaptada al flujo de Builder a partir de:
- `github/awesome-copilot` (`java-springboot`, `spring-boot-testing`, `java-junit`)
  y su issue #1694, que pide cubrir rendimiento JPA, transacciones,
  observabilidad, resiliencia y seguridad en lugar de solo CRUD;
- `Amplicode/spring-skills`, cuya idea central es explorar antes de cambiar y
  detectar las convenciones del proyecto;
- `piomin/claude-ai-spring-boot`;
- `jdubois/dr-jskill` (notas de Spring Boot 4, Jackson 3 y Testcontainers 2);
- la referencia del Scaffold de Bancolombia ya incluida en Builder.

Varias fuentes se contradicen o contienen errores: una plantilla devuelve
entidades JPA desde el controlador, otra usa `@MockBean` deprecado y un mismo
documento usa el paquete antiguo de Testcontainers que él mismo declara
renombrado. Por eso el perfil verifica contra el build y los jars del proyecto.
