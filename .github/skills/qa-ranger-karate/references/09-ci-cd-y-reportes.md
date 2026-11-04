# 09 — Runners, ejecución, reportes y CI/CD

## Contenido
1. Runners (v1 y v2)
2. Paralelismo y aislamiento
3. Selección: tags, ambiente, líneas, nombre, dry run
4. Reportes
5. Logging y enmascaramiento de secretos
6. Pipelines (Azure DevOps, GitHub Actions, Jenkins)
7. Matriz de trazabilidad

---

## 1. Runners

**Runner paralelo para CI (recomendado: uno solo, reporte consolidado)**

v2:
```java
import io.karatelabs.core.Runner;
import io.karatelabs.core.SuiteResult;
import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.assertEquals;

class SuiteTest {
    @Test
    void ejecutarSuite() {
        SuiteResult r = Runner.path("classpath:")
                .tags("~@ignore", "~@wip")
                .outputJunitXml(true)
                .outputCucumberJson(true)
                .outputJsonLines(true)
                .parallel(5);
        assertEquals(0, r.getScenarioFailedCount(), String.join("\n", r.getErrors()));
    }
}
```
v1:
```java
import com.intuit.karate.Results;
import com.intuit.karate.Runner;

class SuiteTest {
    @Test
    void ejecutarSuite() {
        Results r = Runner.path("classpath:").tags("~@ignore", "~@wip")
                .outputJunitXml(true).outputCucumberJson(true).parallel(5);
        assertEquals(0, r.getFailCount(), r.getErrorMessages());
    }
}
```
**Runner por dominio para el IDE**
```java
// v2
class PagosRunner {
    @Karate.Test
    Iterable<DynamicNode> pagos() { return Karate.run("pagos").relativeTo(getClass()); }   // io.karatelabs.junit6.Karate
}
// v1: Karate pagos() { return Karate.run("pagos").relativeTo(getClass()); }            // com.intuit.karate.junit5.Karate
```
Excluye los runners de IDE de la corrida de CI (convención: CI corre solo `SuiteTest`, con `mvn test -Dtest=SuiteTest`).

## 2. Paralelismo

- Hilos: empieza con 4–8 para API; UI según capacidad de navegadores.
- Unidad de paralelismo: **escenario** (no feature). Todo escenario debe ser independiente.
- Serializar recursos compartidos: v2 `@lock=<nombre>` (solo serializa entre los que comparten nombre), `@lock=*` exclusivo total; v1 `@parallel=false` a nivel de feature.
- `callSingle` es seguro entre hilos (se ejecuta una vez); `callonce` es por feature.

## 3. Selección

```bash
mvn test -Dtest=SuiteTest -Dkarate.env=qa -Dkarate.options="--tags @smoke --threads 8"
mvn test -Dtest=SuiteTest -Dkarate.options="classpath:pagos/crear-pago.feature:25"
mvn test -Dtest=SuiteTest -Dkarate.options="--tags @pagos --tags ~@lento"     # AND
mvn test -Dtest=SuiteTest -Dkarate.options="--tags @smoke,@critico"            # OR
mvn test -Dtest=SuiteTest -Dkarate.options="-n 'consulta un pago existente'"   # v2: por nombre
mvn test -Dtest=SuiteTest -Dkarate.options="--dryrun"                          # v2: valida features sin ejecutar
```
`karate.options` **reemplaza** los paths del runner (no suma). Seleccionar por línea o nombre ignora filtros de tags (incluido `@ignore`).

Taxonomía de tags sugerida: nivel (`@smoke`, `@regresion`), dominio (`@pagos`), tipo (`@negativo`, `@seguridad`, `@contrato`), estado (`@wip`, `@bug=JIRA-123`), trazabilidad (`@req=HU-245`), ambiente (`@env=qa`).

## 4. Reportes

| Salida | v1 | v2 |
|---|---|---|
| HTML (`target/karate-reports/karate-summary.html`) | por defecto | por defecto (+ `karate-timeline.html`) |
| JUnit XML (pestaña Tests de Azure/GitHub/Jenkins) | `outputJunitXml(true)` | `outputJunitXml(true)` / `-f junit:xml` |
| Cucumber JSON (Allure, ReportPortal, Xray, cucumber-reporting) | `outputCucumberJson(true)` | `outputCucumberJson(true)` / `-f cucumber:json` |
| `karate-summary.json`, `*.karate-json.txt` | sí | **eliminados** → `karate-json/karate-events.jsonl` |
| JSONL de eventos | — | `outputJsonLines(true)` / `-f karate:jsonl` |

Resumen para notificaciones (v2):
```bash
jq 'select(.type=="SUITE_EXIT") | .data.summary' target/karate-reports/karate-json/karate-events.jsonl
```
Evidencia en reporte: `* karate.embed(bytes, 'image/png')`, `screenshot()` en UI, `print` de identificadores clave (no de payloads con datos sensibles).

## 5. Logging y secretos

v2 (unificado):
```javascript
karate.configure('logging', {
  report: 'debug', console: 'info', pretty: true,
  mask: {
    headers: ['Authorization', 'Cookie', 'X-Api-Key'],
    jsonPaths: ['$.password', '$..token', '$..numeroTarjeta', '$..cvv'],
    patterns: [{ regex: '\\b\\d{13,19}\\b', replacement: '****' }],
    replacement: '***'
  }
});
```
- Escenarios con datos altamente sensibles: tag `@report=false` (v2) — corre y cuenta, sin detalle en artefactos.
- v1: `configure logPrettyRequest/Response`, `configure printEnabled`, y una clase `HttpLogModifier` para enmascarar.
- Los reportes HTML se publican como artefactos del pipeline: trata cualquier dato en ellos como expuesto. En sector financiero, enmascarar PAN/CVV/tokens/documentos es obligatorio, no opcional.

`logback-test.xml` mínimo:
```xml
<configuration>
  <appender name="STDOUT" class="ch.qos.logback.core.ConsoleAppender">
    <encoder><pattern>%d{HH:mm:ss.SSS} [%thread] %-5level %logger{36} - %msg%n</pattern></encoder>
  </appender>
  <logger name="com.intuit.karate" level="INFO"/>   <!-- v1 -->
  <logger name="karate" level="INFO"/>              <!-- v2: karate.http, karate.scenario, karate.runtime -->
  <root level="WARN"><appender-ref ref="STDOUT"/></root>
</configuration>
```

## 6. Pipelines

**Azure DevOps** (`azure-pipelines.yml`):
```yaml
trigger: none
parameters:
  - name: ambiente
    type: string
    default: qa
    values: [dev, qa, stg]
  - name: tags
    type: string
    default: '@smoke'
pool: { vmImage: ubuntu-latest }
variables:
  - group: karate-secrets-${{ parameters.ambiente }}   # CLIENT_ID, CLIENT_SECRET (secretas)
steps:
  - task: JavaToolInstaller@0
    inputs: { versionSpec: '21', jdkArchitectureOption: x64, jdkSourceOption: PreInstalled }
  - task: Maven@4
    displayName: Karate ${{ parameters.ambiente }} ${{ parameters.tags }}
    inputs:
      mavenPomFile: pom.xml
      goals: test
      options: '-Dtest=SuiteTest -Dkarate.env=${{ parameters.ambiente }} "-Dkarate.options=--tags ${{ parameters.tags }}"'
      publishJUnitResults: true
      testResultsFiles: '**/karate-reports/**/*.xml'
    env:
      CLIENT_ID: $(CLIENT_ID)
      CLIENT_SECRET: $(CLIENT_SECRET)
  - publish: target/karate-reports
    artifact: karate-reports-${{ parameters.ambiente }}
    condition: always()
```
(Java 17 + `karate-junit5` si el proyecto es v1. Las variables secretas de Azure no se exponen como env automáticamente: hay que mapearlas en `env:`.)

**GitHub Actions**:
```yaml
name: karate
on: [workflow_dispatch, pull_request]
jobs:
  api:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-java@v4
        with: { distribution: temurin, java-version: '21', cache: maven }
      - run: mvn -B test -Dtest=SuiteTest -Dkarate.env=qa
        env:
          CLIENT_ID: ${{ secrets.CLIENT_ID }}
          CLIENT_SECRET: ${{ secrets.CLIENT_SECRET }}
      - uses: actions/upload-artifact@v4
        if: always()
        with: { name: karate-reports, path: target/karate-reports }
```

**Jenkins**: `sh 'mvn test -Dtest=SuiteTest -Dkarate.env=qa'` + `junit 'target/karate-reports/**/*.xml'` + `publishHTML` sobre `karate-summary.html` (o plugin cucumber-reports con el Cucumber JSON).

Política recomendada: `@smoke` en cada despliegue (bloqueante), regresión completa nocturna, contratos en el pipeline del proveedor.

## 7. Matriz de trazabilidad

Con escenarios nombrados `[HU-245][CA-3] ...` o etiquetados `@req=HU-245/CA-3`, ejecuta:
```bash
python scripts/rtm_from_cucumber.py target/karate-reports --out rtm.md
```
(requiere Cucumber JSON habilitado). Genera tabla requisito → criterio → escenarios → estado, y lista los escenarios sin trazabilidad.
