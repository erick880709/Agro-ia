# 08 — CI/CD

## 1. Qué correr en el pipeline
- **En cada release**: prueba de regresión de rendimiento corta (5–15 min, carga moderada y estable) contra un ambiente dedicado, comparada con la base. Es la que detecta "este cambio hizo el endpoint 40 % más lento".
- **Programadas** (nocturnas/semanales): carga completa, estrés, resistencia.
- No en cada commit (costo y ruido), salvo pruebas de humo de 1–2 min con JMeter DSL (09).

## 2. Gate
1. Ejecutar JMeter en CLI.
2. `analizar_jtl.py --sla sla.json --base base.jtl` → código de salida ≠ 0 si falla.
3. Publicar el dashboard HTML y el resumen como artefactos (siempre, también si falla).
4. Actualizar la base solo tras una ejecución aprobada y revisada (no automáticamente en cada corrida verde).

## 3. GitHub Actions
```yaml
name: rendimiento
on:
  workflow_dispatch:
    inputs:
      ambiente: { type: choice, options: [qa, stg], default: qa }
      usuarios: { type: string, default: '20' }
jobs:
  jmeter:
    runs-on: ubuntu-latest           # o self-hosted con capacidad verificada y en la red del ambiente
    timeout-minutes: 60
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-java@v4
        with: { distribution: temurin, java-version: '17' }
      - name: Instalar JMeter (versión fijada y verificada)
        run: |
          curl -sSLO https://archive.apache.org/dist/jmeter/binaries/apache-jmeter-5.6.3.tgz
          curl -sSL https://archive.apache.org/dist/jmeter/binaries/apache-jmeter-5.6.3.tgz.sha512 | awk '{print $1"  apache-jmeter-5.6.3.tgz"}' | sha512sum -c -
          tar xzf apache-jmeter-5.6.3.tgz
      - name: Ejecutar
        run: |
          apache-jmeter-5.6.3/bin/jmeter -n -t plan.jmx -q env/${{ inputs.ambiente }}.properties \
            -Jusuarios=${{ inputs.usuarios }} -Jclave="$CLAVE" -l resultados/resultados.jtl -f -e -o resultados/reporte
        env: { CLAVE: '${{ secrets.CLAVE_QA }}' }
      - name: Gate SLA
        run: python3 scripts/analizar_jtl.py resultados/resultados.jtl --sla sla.json --base base/base.jtl --md resultados/resumen.md
      - name: Resumen en el job
        if: always()
        run: cat resultados/resumen.md >> "$GITHUB_STEP_SUMMARY" || true
      - uses: actions/upload-artifact@v4
        if: always()
        with: { name: resultados-rendimiento, path: resultados/ }
```
Alternativa: la action `QAInsights/PerfAction` (ejecuta JMeter en un contenedor con `test-plan-path`, `results-file`, `args`); fija su versión por SHA y aplica el gate con `analizar_jtl.py` después.

## 4. Azure DevOps
```yaml
trigger: none
parameters:
  - name: ambiente
    type: string
    default: qa
    values: [qa, stg]
  - name: usuarios
    type: string
    default: '20'
pool: { name: generadores-carga }                 # agentes self-hosted en la red del ambiente
variables:
  - group: rendimiento-${{ parameters.ambiente }}  # CLAVE (secreta)
steps:
  - script: |
      $(JMETER_HOME)/bin/jmeter -n -t plan.jmx -q env/${{ parameters.ambiente }}.properties \
        -Jusuarios=${{ parameters.usuarios }} -Jclave="$CLAVE" -l resultados/resultados.jtl -f -e -o resultados/reporte
    displayName: Ejecutar JMeter
    env: { CLAVE: $(CLAVE) }                      # secretas mapeadas explícitamente
  - script: python3 scripts/analizar_jtl.py resultados/resultados.jtl --sla sla.json --base base/base.jtl --md resultados/resumen.md --junit resultados/junit-sla.xml
    displayName: Gate SLA
  - task: PublishTestResults@2
    condition: always()
    inputs: { testResultsFormat: JUnit, testResultsFiles: resultados/junit-sla.xml, testRunTitle: SLA rendimiento }
  - publish: resultados
    artifact: resultados-rendimiento
    condition: always()
```
`--junit` convierte cada criterio del SLA en un caso de prueba: aparece en la pestaña Tests de Azure DevOps/Jenkins.

## 5. Jenkins
`sh` con el mismo comando, `junit 'resultados/junit-sla.xml'`, `publishHTML` sobre `resultados/reporte/index.html`, y opcionalmente el plugin **Performance** para tendencias entre builds.

## 6. Generadores en CI
Los runners compartidos tienen CPU limitada y red variable: válidos para humo y regresión ligera, **no** para carga real. Para carga, agentes dedicados en la misma red/región que el ambiente, con capacidad medida (12).
