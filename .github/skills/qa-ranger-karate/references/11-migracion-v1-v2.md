# 11 — Migración Karate v1 → v2

Fuente: `docs/MIGRATION_GUIDE.md` del repo `karatelabs/karate` (rama `main`). v2 es una reescritura completa con shims de compatibilidad; en la mayoría de proyectos basta cambiar dependencias y Java.

## Procedimiento recomendado

1. **Inventario** (antes de tocar nada): versión actual, Java, build tool, runners, uso de `@parallel=false`, consumidores de reportes JSON (dashboards, scripts de CI), `HttpLogModifier`, driver/UI, `karate-robot`, Gatling, servidor HTTP embebido, `karate.toJava`, `JsonUtils`.
   ```bash
   grep -rn "@parallel=false" src/test
   grep -rn "karate-summary.json\|json.txt" .        # scrapers a reescribir
   grep -rln "karate-robot\|com.intuit.karate.robot" .   # bloqueante: no existe en v2
   grep -rn "toJava\|HttpLogModifier\|JsonUtils\|WebSocketClient" src/test
   ```
2. **Fase 1 — dependencias** (los shims hacen el resto):
   - `karate-junit5` → `karate-junit6` + `junit-jupiter` explícito.
   - Java 21 (`maven.compiler.release=21`), surefire 3.2.5+.
   - Gatling: `--add-opens=java.base/java.lang=ALL-UNNAMED` en `jvmArgs`.
   - Correr la suite completa y comparar resultados con la última corrida v1 (mismo ambiente).
3. **Fase 2 — cambios de comportamiento obligatorios**:
   - `@parallel=false` → `@lock=<nombre>` (o `@lock=*`). **Se ignora en silencio en v2**: no esperes un error.
   - Reportes: `outputJunitXml(true)` / `outputCucumberJson(true)` si el pipeline los consume (ya no salen por defecto). Reescribir scrapers de `karate-summary.json` hacia `karate-events.jsonl`.
   - Logging: `logPrettyRequest/Response`, `printEnabled`, `lowerCaseResponseHeaders`, `logModifier` → `configure logging = { ... }`.
   - Gatling: variables de sesión solo con prefijo `__gatling.` / `__karate.`.
   - Cookies: dominios con punto inicial se normalizan (`.ejemplo.com` → `ejemplo.com`).
   - RHS que dependía de semántica JS sin paréntesis (`{ id: pathParams.id }`): usar `#(...)` o `({ ... })`.
   - UI: `element.parent/children/...` → `closest()` / `locateAll()` / `script()`; `delay()` antes del driver → `karate.pause()`.
   - Imagen: `compareImage` → extensión `karate-image` (`image.compare(...)`) activada en `karate-boot.js`.
   - Servidor HTTP embebido como backend de pruebas → `MockServer` con feature.
4. **Fase 3 — APIs nativas** (eliminar warnings de deprecación):

| v1 | v2 |
|---|---|
| `com.intuit.karate.Runner` / `Results` | `io.karatelabs.core.Runner` / `SuiteResult` |
| `getFailCount()` / `getErrorMessages()` | `getScenarioFailedCount()` / `String.join("\n", getErrors())` |
| `com.intuit.karate.junit5.Karate`, retorno `Karate` | `io.karatelabs.junit6.Karate`, retorno `Iterable<DynamicNode>` |
| `MockServer...http(0).build()` / `.arg(k, v)` | `MockServer...start()` / `.arg(Map.of(k, v))`, `.stopAndWait()` |
| `com.intuit.karate.gatling.javaapi.KarateDsl` | `io.karatelabs.gatling.KarateDsl` |
| `pauseFor("get", 10)` | `pauseFor(method("get", 10))` |
| `Supplier` como binding lazy | `JsLazy` |

5. **Validación**: misma cantidad de escenarios ejecutados, mismos resultados, tiempos comparables, reportes consumidos correctamente por el pipeline.

## Bloqueantes para migrar

- Uso de `karate-robot` (automatización desktop): no existe en v2.
- Plataforma anclada a Java < 21 sin posibilidad de toolchain separado para pruebas. (Nota: el módulo de pruebas puede tener su propio JDK aunque el servicio use 17, si el pipeline lo permite.)
- Dependencia de extensiones comerciales aún no publicadas para v2: verificar con Karate Labs.

## Entregable sugerido

Informe con: inventario, cambios por fase (archivo y línea), riesgos, resultado comparativo de ejecución v1 vs v2 y plan de rollback (rama con v1 hasta estabilizar).
