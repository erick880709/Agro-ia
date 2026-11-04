# 08 — CI/CD y reportes

## 1. Maven
```bash
mvn -B test -Denv=qa -Dbrowser=chrome -Dheadless=true -Dgroups=smoke          # JUnit 5 por tags
mvn -B test -Denv=qa -DsuiteXmlFile=testng-smoke.xml                           # TestNG
mvn -B test -Dtest='Transferencia*Test'                                        # por clase
```
Surefire genera JUnit XML en `target/surefire-reports/` (lo consumen Azure, Jenkins, GitHub). Configura `-Dsurefire.failIfNoSpecifiedTests=false` si filtras por tags.

**Importante para la trazabilidad**: por defecto Surefire escribe en el XML el *nombre del método*, no el `@DisplayName`. Para que los IDs `[HU-x][CA-y]` del `@DisplayName` lleguen al reporte del CI y a la matriz:
```xml
<plugin>
  <groupId>org.apache.maven.plugins</groupId>
  <artifactId>maven-surefire-plugin</artifactId>
  <version>${surefire.version}</version>
  <configuration>
    <statelessTestsetReporter implementation="org.apache.maven.plugin.surefire.extensions.junit5.JUnit5Xml30StatelessReporter">
      <usePhrasedTestCaseMethodName>true</usePhrasedTestCaseMethodName>
      <usePhrasedTestSuiteClassName>true</usePhrasedTestSuiteClassName>
    </statelessTestsetReporter>
  </configuration>
</plugin>
```
La plantilla `java-junit5` ya lo incluye.

## 2. Azure DevOps (con docker-selenium como servicio)
```yaml
trigger: none
parameters:
  - name: ambiente
    type: string
    default: qa
    values: [dev, qa, stg]
  - name: grupos
    type: string
    default: smoke
pool: { vmImage: ubuntu-latest }
variables:
  - group: ui-secrets-${{ parameters.ambiente }}         # E2E_USER, E2E_PASSWORD (secretas)
resources:
  containers:
    - container: chrome
      image: selenium/standalone-chrome:latest          # fijar etiqueta exacta
      ports: ['4444:4444']
      options: --shm-size=2g
services:
  chrome: chrome
steps:
  - task: JavaToolInstaller@0
    inputs: { versionSpec: '17', jdkArchitectureOption: x64, jdkSourceOption: PreInstalled }
  - script: until curl -sf http://localhost:4444/status | grep -q '"ready": true'; do sleep 2; done
    displayName: Esperar Selenium Grid
    timeoutInMinutes: 3
  - task: Maven@4
    displayName: Pruebas UI ${{ parameters.ambiente }}
    inputs:
      mavenPomFile: pom.xml
      goals: test
      options: '-Denv=${{ parameters.ambiente }} -Dgroups=${{ parameters.grupos }} -DgridUrl=http://localhost:4444 -Dheadless=true'
      publishJUnitResults: true
      testResultsFiles: '**/surefire-reports/TEST-*.xml'
    env:
      E2E_USER: $(E2E_USER)                              # mapear secretas explícitamente
      E2E_PASSWORD: $(E2E_PASSWORD)
  - publish: target/evidencia
    artifact: evidencia-ui
    condition: failed()
```
Si la app bajo prueba no es accesible desde el contenedor del navegador, usa agentes self-hosted en la red corporativa o el Grid corporativo.

## 3. GitHub Actions
```yaml
jobs:
  ui:
    runs-on: ubuntu-latest
    services:
      selenium:
        image: selenium/standalone-chrome:latest
        ports: ['4444:4444']
        options: --shm-size=2g
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-java@v4
        with: { distribution: temurin, java-version: '17', cache: maven }
      - run: until curl -sf http://localhost:4444/status | grep -q '"ready": true'; do sleep 2; done
      - run: mvn -B test -Denv=qa -DgridUrl=http://localhost:4444
        env: { E2E_USER: '${{ secrets.E2E_USER }}', E2E_PASSWORD: '${{ secrets.E2E_PASSWORD }}' }
      - uses: actions/upload-artifact@v4
        if: always()
        with:
          name: reportes
          path: |
            target/surefire-reports/
            target/evidencia/
```
(Alternativa sin Grid: `browser-actions/setup-chrome` y driver local vía Selenium Manager.)

## 4. Reportes
| Herramienta | Uso |
|---|---|
| JUnit XML (Surefire / TestNG / pytest `--junitxml`) | Pestaña de tests del CI, trazabilidad (§5) |
| Allure (`allure-junit5`, `allure-testng`, `allure-pytest`) | Reporte navegable con pasos, adjuntos (screenshots) e historial |
| Extent Reports | Alternativa común en equipos TestNG |
| pytest-html | Reporte HTML simple en Python |

Adjunta screenshot y page source **solo en fallos**, y nunca credenciales.

## 5. Trazabilidad
Nombres con IDs (`@DisplayName("[HU-245][CA-1] ...")`, `@Tag("HU-245")`, o `description` en TestNG). Matriz desde los XML:
```bash
python scripts/rtm_from_junit.py target/surefire-reports --out rtm.md --csv rtm.csv
python scripts/rtm_from_junit.py reports/junit.xml          # pytest --junitxml
```
