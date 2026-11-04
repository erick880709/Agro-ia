# Runners y cobertura

Comandos para ejecutar unitarias con cobertura y reporte JUnit, por runner.
Adapta rutas al proyecto y guarda los reportes en `resources/qa/unit/<runId>/`.
Verifica cada opción contra la versión instalada (`--help`) antes de fijarla.

## Métricas que reporta cada herramienta

El validador Node identifica las métricas soportadas en el reporte nativo.

| Runner | Herramienta de cobertura | Formato recomendado | Métricas |
|---|---|---|---|
| Vitest | `@vitest/coverage-v8` o `-istanbul` | `json-summary` o `lcov` | json-summary: las cuatro; lcov: líneas, ramas, funciones |
| Jest | Istanbul integrado | `json-summary` o `lcov` | json-summary: las cuatro; lcov: líneas, ramas, funciones |
| Node.js test runner | integrada (`--experimental-test-coverage`) | `lcov` | líneas, ramas, funciones |
| pytest | `pytest-cov` (coverage.py) | Cobertura XML | líneas, ramas (solo con `--cov-branch`) |
| JUnit 5 | JaCoCo | XML | líneas, ramas, métodos como funciones |
| xUnit/NUnit/MSTest | coverlet | Cobertura XML | líneas, ramas |

Prefiere `json-summary` en Jest y Vitest: conserva sentencias. JaCoCo no reporta
sentencias; sus instrucciones de bytecode no se presentan como sentencias.

## JavaScript y TypeScript

**Vitest**

```bash
npx vitest run --coverage --coverage.reporter=json-summary --coverage.reporter=lcov \
  --coverage.reportsDirectory=resources/qa/unit/<runId>/coverage \
  --reporter=default --reporter=junit --outputFile.junit=resources/qa/unit/<runId>/junit.xml
```

Requiere el paquete de cobertura del proveedor configurado. Vitest excluye los
archivos de prueba de la cobertura por defecto.

**Jest**

```bash
npx jest --coverage --coverageReporters=json-summary --coverageReporters=lcov \
  --coverageDirectory=resources/qa/unit/<runId>/coverage --reporters=default --reporters=jest-junit
```

`jest-junit` es un paquete aparte; su salida se fija con `JEST_JUNIT_OUTPUT_DIR`.
Usa `collectCoverageFrom` para medir también los archivos que ninguna prueba importa;
sin él, un módulo sin pruebas no aparece en el denominador.

**Node.js test runner (Node 22+)**

```bash
node --test --experimental-test-coverage --test-coverage-exclude="**/*.test.*" \
  --test-reporter=spec --test-reporter-destination=stdout \
  --test-reporter=lcov --test-reporter-destination=resources/qa/unit/<runId>/lcov.info \
  --test-reporter=junit --test-reporter-destination=resources/qa/unit/<runId>/junit.xml
```

Sin `--test-coverage-exclude`, los archivos de prueba entran en la medición.
Con versiones que no tienen esa opción, usa `--exclude` de `unit_report.py`.

## Python

```bash
pytest --cov=<paquete> --cov-branch \
  --cov-report=xml:resources/qa/unit/<runId>/coverage.xml \
  --junitxml=resources/qa/unit/<runId>/junit.xml
```

Sin `--cov-branch`, coverage.py escribe `branches-valid="0"`: las ramas quedan
desconocidas y la meta no se acredita. `--cov=<paquete>` limita la medición al
código bajo prueba.

## Java

Maven con JaCoCo configurado (`prepare-agent` y `report`):

```bash
mvn test jacoco:report
# cobertura: target/site/jacoco/jacoco.xml · resultados: target/surefire-reports/TEST-*.xml
```

Gradle con el plugin `jacoco` y `xml.required = true`:

```bash
gradle test jacocoTestReport
# cobertura: build/reports/jacoco/test/jacocoTestReport.xml · resultados: build/test-results/test/*.xml
```

Surefire y Gradle escriben un XML por clase: pasa todos a `unit_report.py junit`.
Separa las pruebas de integración (Failsafe, `*IT`) del reporte unitario.

## .NET

```bash
dotnet test --collect:"XPlat Code Coverage" --results-directory resources/qa/unit/<runId> \
  --logger "junit;LogFilePath=resources/qa/unit/<runId>/junit.xml"
```

El colector de coverlet escribe `coverage.cobertura.xml` dentro de una subcarpeta
por corrida. El logger JUnit requiere el paquete `JunitXml.TestLogger`; sin él,
convierte el TRX con una herramienta compatible; no transcribas conteos de consola.

## Entregar los reportes al contrato

Usa el reporter CTRF del runner, o convierte el JUnit XML nativo a CTRF.
Declara el archivo CTRF como `test_results` y el reporte nativo de cobertura
como `coverage_report`, ambos con `path` dentro de `resources/qa/`.
En `data` usa `coverage: {scope: "src/pricing"}` y `targetOverride: null`.
No añadas conteos, `verification` ni `execution`: Node lee los reportes.

`coverage.include` y `coverage.exclude` filtran archivos en LCOV e Istanbul;
en XML ajusta el alcance en la herramienta de cobertura. El reporte debe
corresponder exclusivamente a pruebas unitarias y excluir archivos de tests.
Declara `expected` con los casos acordados (o `null` si se desconocen), y
`evidencePolicy` de nivel `unit`.

`scripts/unit_report.py` conserva su uso independiente para análisis; sus
bloques antiguos no corresponden al contrato vigente. Una suite vacía,
solo omitida o con fallos no acredita implementación satisfactoria.
Si el reporte es inválido, conserva el error y vuelve a generarlo con el runner;
no completes sus conteos manualmente para acreditar la meta.
