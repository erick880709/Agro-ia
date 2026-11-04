# 06 — Ejecución

## 1. CLI (siempre para carga)
```bash
jmeter -n -t plan.jmx \
  -q env/qa.properties -Jusuarios=100 -Jrampa=300 -Jduracion=1800 \
  -l resultados/resultados.jtl -j resultados/jmeter.log \
  -f -e -o resultados/reporte
```
`-n` sin GUI · `-t` plan · `-q` propiedades del ambiente · `-J` sobreescrituras · `-l` resultados · `-j` log · `-f` sobrescribe resultados y reporte previos · `-e -o` dashboard HTML al terminar.
Reporte desde un JTL existente: `jmeter -g resultados.jtl -o reporte/`.

Secuencia obligatoria antes de una prueba real:
1. `lint_jmx.py plan.jmx` sin hallazgos bloqueantes.
2. `-Jusuarios=1 -Jduracion=60` → 0 % de errores, respuestas correctas (revisar el JTL o habilitar un View Results Tree solo en esta corrida desde la GUI).
3. Humo con pocos usuarios.
4. Prueba real, con monitoreo del servidor activo y criterio de aborto acordado.

Detener una prueba: `bin/shutdown.sh` (cierre ordenado) o `bin/stoptest.sh` (inmediato), desde la máquina del generador.

## 2. Generador: capacidad y señales
Un generador saturado mide **su propia** lentitud. Durante la prueba vigila CPU (< 70–80 %), memoria (GC), red y sockets del generador. Si se satura: más generadores (distribuido), menos trabajo por muestra (sin listeners, scripting mínimo) o más heap. Ver 12.

## 3. Distribuida
Controlador + N generadores (`jmeter-server`):
```bash
# en cada generador
jmeter-server -Djava.rmi.server.hostname=10.0.0.11
# en el controlador
jmeter -n -t plan.jmx -R 10.0.0.11,10.0.0.12 -Gusuarios=50 -Gduracion=1800 -l resultados.jtl -X
```
- `-G` envía propiedades a los generadores (`-J` solo aplica al controlador). **Los hilos son por generador**: 50 hilos × 2 generadores = 100.
- Misma versión de JMeter, Java y plugins en todos; CSV en cada nodo (subconjuntos distintos).
- RMI requiere keystore (`bin/create-rmi-keystore.sh`) o `server.rmi.ssl.disable=true` solo en redes aisladas.
- Alternativa más simple y escalable: N contenedores independientes ejecutando el mismo plan en modo `-n` y unir los JTL al final (`cat` respetando un solo encabezado) antes de analizarlos.

## 4. Docker
```bash
docker run --rm -v "$PWD":/prueba -w /prueba <imagen-jmeter:5.6.3> \
  -n -t plan.jmx -q env/qa.properties -l resultados/resultados.jtl -e -o resultados/reporte
```
Limita recursos explícitamente y asegúrate de que el contenedor tenga suficiente CPU: un contenedor con 1 vCPU satura antes que el sistema bajo prueba.

## 5. Taurus (bzt)
Envoltorio YAML que ejecuta JMeter (y otros motores), con criterios de aprobación integrados:
```yaml
execution:
- scenario: plan
  concurrency: 50
  ramp-up: 5m
  hold-for: 30m
scenarios:
  plan:
    script: plan.jmx
reporting:
- module: passfail
  criteria:
  - p95>1200ms for 30s, stop as failed
  - fail>1% for 1m, stop as failed
```
`bzt prueba.yml -o modules.jmeter.version=5.6.3`. Útil cuando se quieren criterios de aborto en tiempo real; si no, `analizar_jtl.py` cubre el gate posterior.
