# 12 — Troubleshooting

| Síntoma | Causa probable | Solución |
|---|---|---|
| `could not find karate-config.js` o variables `baseUrl` indefinidas | `karate-config.js` no está en la raíz del classpath de pruebas, o falta el bloque `testResources` que copia `src/test/java` | Mover a `src/test/java/` (o `src/test/resources/`) y verificar `testResources` en el pom / `sourceSets` en Gradle |
| `.feature` no encontrado con `classpath:` | Features en `src/test/java` sin `testResources` configurado | Agregar bloque `testResources` (ver 01) |
| Valor `'id'` (string) en lugar del valor de la variable | Regla del RHS: `{ id: id }` | `{ id: '#(id)' }` o `({ id: id })` |
| `ReferenceError: # is not defined` | Placeholder `#(x)` sin comillas en un contexto evaluado como JS | Poner entre comillas `'#(x)'` o usar literal JSON |
| `<function> is not defined` (click, input...) | Función de driver usada antes de `driver 'url'` | Inicializar el driver antes; sin driver usar `karate.pause` |
| Pruebas pasan solas y fallan en paralelo | Datos compartidos/colisiones, dependencia de orden, estado global mutable | Datos únicos por escenario; `@lock`; revisar variables en `karate-config.js` mutadas en features |
| `@parallel=false` no tiene efecto | Proyecto en v2 | `@lock=<nombre>` |
| Escenarios que deberían correr no corren | Tags: `~@ignore` heredado, `@env=` que no coincide, `karate.options` reemplazando paths | Revisar log `karate.options applied` (v2), `karate.env` efectivo |
| Escenario marcado como saltado | `karate.abort()` o fallo en Background | Revisar el primer paso fallido en el HTML |
| `javax.net.ssl.SSLHandshakeException` / PKIX | Certificado no confiable | `configure ssl = true` (ambientes bajos) o truststore explícito; mTLS con keystore |
| `ConnectException` / timeouts desde CI y no local | Proxy corporativo, firewall, DNS interno | `configure proxy`, agentes self-hosted en la red, `nonProxyHosts` |
| Token expira en suites largas | `callSingle` lo cacheó al inicio | Headers por función con renovación según `exp` |
| `callSingle` se ejecuta varias veces | Clave (primer argumento) distinta o llamadas desde diferentes JVM | Misma clave para el mismo perfil; claves con sufijo ?admin/?cliente para perfiles distintos; un único runner |
| `match` falla por orden de arreglo | `==` respeta orden | `contains only` |
| Números: `1000` vs `1000.0` o `BigDecimal` de Oracle | Tipos numéricos distintos | `'#? _ == 1000'` o convertir |
| Fechas que fallan según zona horaria del agente CI | `LocalDate.now()` en servidor UTC | Fijar zona: `java.time.ZoneId.of('America/Bogota')` |
| `IllegalAccessException: module java.base does not open java.lang` en Gatling | Gatling 4.7+ en Java 17/21 | `--add-opens=java.base/java.lang=ALL-UNNAMED` |
| Variables de Gatling undefined en v2 | Acceso sin prefijo | `__gatling.x` / `karate.get('__gatling.x', def)` |
| JUnit XML no aparece en v2 | Opt-in | `outputJunitXml(true)` / `-f junit:xml` |
| No hay `karate-summary.json` en v2 | Eliminado | `karate-json/karate-events.jsonl` |
| `karate-junit6` no compila / no encuentra JUnit | JUnit es `provided` | Agregar `org.junit.jupiter:junit-jupiter` |
| Karate 1.4.x/1.5.1 falla al arrancar con Java reciente | Incompatibilidad del motor JS | Karate 1.5.2 (o v2 en Java 21) |
| Licencia: `license check` al iniciar Kafka/gRPC/Agent | Extensión comercial sin `.karate/karate.lic` | Solicitar licencia a Karate Labs o usar Java interop |
| UI flaky | Esperas implícitas inexistentes, selectores frágiles | `waitFor*`, `retry()`, `data-testid` |

## Diagnóstico rápido

1. Abrir `target/karate-reports/karate-summary.html` → feature → primer paso rojo: muestra request/response completos (en v2 los bodies están en el HTML por defecto).
2. Reproducir aislado: `-Dkarate.options="ruta.feature:LINEA"`.
3. Más detalle en consola: v2 `--log-console trace` (bodies) o `configure logging = { console: 'debug' }` dentro del escenario; v1 logger `com.intuit.karate` en DEBUG.
4. Validar sintaxis sin ejecutar: v2 `--dryrun`.
5. Verificar ambiente efectivo: `* print karate.env, baseUrl` al inicio.
