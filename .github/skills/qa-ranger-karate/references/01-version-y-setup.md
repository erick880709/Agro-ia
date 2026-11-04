# 01 — Versión y setup

## Contenido
1. Matriz de decisión v1 vs v2
2. Dependencias Maven v2
3. Dependencias Maven v1
4. Gradle
5. CLI standalone (equipos sin Java/Maven)
6. `karate-pom.json`
7. Estructura de proyecto recomendada
8. Scaffold Clean Architecture de Bancolombia

---

## 1. Matriz de decisión

| Criterio | v1 (1.5.2) | v2 (2.x) |
|---|---|---|
| Java mínimo | 11 (1.5.x soporta hasta Java 24 desde 1.5.2) | **21** (usa virtual threads) |
| groupId | `io.karatelabs` (desde 1.4) | `io.karatelabs` |
| Runner JUnit | `karate-junit5` (trae JUnit embebido) | `karate-junit6` (JUnit `provided`: agregar `junit-jupiter` explícito) |
| Motor JS | GraalJS | Motor propio `karate-js` (thread-safe) |
| Serializar escenarios | `@parallel=false` | `@lock=<nombre>` / `@lock=*` (`@parallel=false` se **ignora en silencio**) |
| Reportes por defecto | HTML + JSON + Cucumber JSON | Solo HTML; JUnit XML, Cucumber JSON y JSONL son opt-in |
| UI desktop (karate-robot) | Sí | **No** |
| Estado | Mantenimiento | Desarrollo activo |

Regla práctica: si el proyecto ya corre en Java 21, v2. Si está anclado a Java 17 (habitual en ecosistemas bancarios y en proyectos generados por el scaffold Bancolombia), v1.5.2 hasta que el stack suba a 21.

Notas de compatibilidad Java para v1: Karate 1.4.1 no funciona con Java 22+; 1.5.1 no funciona con Java 24+; usar 1.5.2.

## 2. Maven v2

```xml
<properties>
    <java.version>21</java.version>
    <karate.version>2.1.3</karate.version>
    <junit.version>6.1.3</junit.version>
    <maven.surefire.version>3.5.2</maven.surefire.version>
</properties>

<dependencies>
    <dependency>
        <groupId>io.karatelabs</groupId>
        <artifactId>karate-junit6</artifactId>
        <version>${karate.version}</version>
        <scope>test</scope>
    </dependency>
    <dependency>
        <!-- karate-junit6 declara junit-jupiter como provided -->
        <groupId>org.junit.jupiter</groupId>
        <artifactId>junit-jupiter</artifactId>
        <version>${junit.version}</version>
        <scope>test</scope>
    </dependency>
</dependencies>

<build>
    <testResources>
        <!-- convención Karate: features junto a las clases Java -->
        <testResource>
            <directory>src/test/java</directory>
            <excludes><exclude>**/*.java</exclude></excludes>
        </testResource>
    </testResources>
    <plugins>
        <plugin>
            <groupId>org.apache.maven.plugins</groupId>
            <artifactId>maven-compiler-plugin</artifactId>
            <version>3.13.0</version>
            <configuration><release>${java.version}</release></configuration>
        </plugin>
        <plugin>
            <!-- 3.2.5+ requerido para JUnit 6 -->
            <groupId>org.apache.maven.plugins</groupId>
            <artifactId>maven-surefire-plugin</artifactId>
            <version>${maven.surefire.version}</version>
        </plugin>
    </plugins>
</build>
```

`karate-core` solo se agrega explícito si se usa el servidor HTTP embebido o APIs del core en código de `main`. Para Gatling: `io.karatelabs:karate-gatling` (ver 07).

Versión verificada al crear la skill: 2.1.3 estable (main en 2.1.4.RC1). Confirmar la última en Maven Central.

## 3. Maven v1

```xml
<properties>
    <java.version>17</java.version>
    <karate.version>1.5.2</karate.version>
</properties>
<dependencies>
    <dependency>
        <groupId>io.karatelabs</groupId>
        <artifactId>karate-junit5</artifactId>
        <version>${karate.version}</version>
        <scope>test</scope>
    </dependency>
</dependencies>
```
Mismo bloque `testResources`. Surefire 3.x.

## 4. Gradle (Groovy DSL)

```groovy
plugins { id 'java' }

java { toolchain { languageVersion = JavaLanguageVersion.of(17) } } // 21 para v2

ext { karateVersion = '1.5.2' }

dependencies {
    testImplementation "io.karatelabs:karate-junit5:${karateVersion}"
    // v2: testImplementation "io.karatelabs:karate-junit6:2.1.3"
    //     testImplementation "org.junit.jupiter:junit-jupiter:6.1.3"
}

sourceSets {
    test {
        resources {
            srcDir file('src/test/java')
            exclude '**/*.java'
        }
    }
}

test {
    useJUnitPlatform()
    systemProperty 'karate.options', System.properties.getProperty('karate.options')
    systemProperty 'karate.env', System.properties.getProperty('karate.env')
    outputs.upToDateWhen { false }   // siempre re-ejecutar
}
```
Ejecutar: `./gradlew test -Dkarate.env=qa -Dkarate.options="--tags @smoke"`.

## 5. CLI standalone (v2)

Para equipos sin Java/Maven: el CLI (`karate.sh`) descarga JRE y JAR.

```bash
curl -fsSL https://karate.sh/install.sh | sh      # macOS/Linux
irm https://karate.sh/install.ps1 | iex           # Windows PowerShell
karate setup            # descarga JRE + JAR
karate doctor           # diagnóstico
karate run features/    # .feature y .karate.js
karate run -t @smoke -e qa -T 5 features/
karate mock -m users.feature -p 8080
```
Opciones de `run`: `-P/--path`, `-t/--tags`, `-T/--threads`, `-e/--env`, `-n/--name` (nombre exacto de escenario), `-o/--output`, `-g/--configdir`, `-C/--clean`, `-D/--dryrun`, `-f/--format` (`html`, `cucumber:json`, `junit:xml`, `karate:jsonl`; prefijo `~` desactiva), `--log-report`, `--log-console`. `archivo.feature:10:25` corre escenarios por línea (ignora filtros de tags).

Archivos `*.karate.js`: scripts JS con la API `karate.*` completa, útiles para orquestación, procesos y flujos async.

## 6. `karate-pom.json` (v2, solo CLI)

Define *cómo* correr (no reemplaza `karate-config.js`, que define *con qué* datos). Para equipos Java se usa `Runner.Builder` + system properties.

```json
{
  "paths": ["features/"],
  "tags": ["~@ignore", "~@wip"],
  "env": "dev",
  "threads": 5,
  "output": { "dir": "target/karate-reports", "html": true, "junitXml": true, "jsonLines": true },
  "logging": { "report": "debug", "console": "info" }
}
```
Precedencia: flags CLI → `karate-pom.json` → defaults.

## 7. Estructura recomendada

```
src/test/java/
├── karate-config.js            # config por ambiente (obligatorio en la raíz del classpath)
├── karate-config-qa.js         # opcional: override por ambiente
├── logback-test.xml
└── <dominio>/                  # p.ej. pagos/, clientes/
    ├── <Dominio>Test.java      # runner del dominio (o un único runner global)
    ├── features/
    │   ├── crear-pago.feature
    │   └── consultar-pago.feature
    ├── common/                 # features @ignore reutilizables (auth, setup de datos)
    ├── schemas/                # esquemas JSON para match
    └── data/                   # payloads, CSV de casos
```
Un runner global con `parallel(n)` para CI (genera un único reporte consolidado) y runners por dominio solo para ejecución local desde el IDE.

## 8. Scaffold Clean Architecture de Bancolombia

El plugin Gradle del scaffold incluye la tarea `generateAcceptanceTest` (alias `gat`), que genera un subproyecto de pruebas de aceptación basado en Karate dentro de `deployment/`. Al trabajar con un proyecto generado así:
- Revisa la versión de Karate y Java que trae el subproyecto generado (depende de la versión del plugin) antes de proponer cambios; normalmente es la línea v1.
- Respeta su estructura y `build.gradle` en lugar de imponer la estructura de la sección 7.
- Las pruebas apuntan al microservicio desplegado (URL por ambiente en `karate-config.js`).
