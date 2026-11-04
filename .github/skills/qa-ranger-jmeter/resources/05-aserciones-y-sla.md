# 05 — Aserciones y criterios de aceptación

## 1. Aserciones: pocas y baratas
Cada aserción consume CPU del generador en cada muestra. Valida lo suficiente para no contar como éxito una respuesta errónea:

| Aserción | Uso | Notas |
|---|---|---|
| **Response Assertion** | Código HTTP o texto esperado | Propiedades: `Assertion.test_field`, `Assertion.test_type`, **`Asserion.test_strings`** (errata histórica: no corregir) |
| JSON Assertion (`JSONPathAssertion`) | Campo JSON con valor | `JSON_PATH`, `EXPECTED_VALUE`, `JSONVALIDATION` |
| Duration Assertion | Marca como fallida una muestra lenta | `DurationAssertion.duration` (ms). Úsala con cuidado: mezcla errores funcionales con SLA |
| Size Assertion | Tamaño de respuesta | |

Evita en carga: XPath sobre respuestas grandes, aserciones JSR223 pesadas, comparaciones de cuerpos completos.

Valores de `Assertion.test_type` (bits, verificados en `ResponseAssertion.java`): 1 = Matches, 2 = Contains, 8 = Equals, 16 = Substring; sumar 4 para negar (NOT) y 32 para combinar patrones con OR (por defecto AND). Ejemplo: 16 = "contiene la subcadena"; 20 = "NO contiene". `Assertion.test_field`: `Assertion.response_code`, `Assertion.response_data`, `Assertion.response_headers`, etc.

## 2. Por qué un 200 no basta
Muchas APIs devuelven 200 con un cuerpo de error (`{"codigo":"ERROR"}`) o una página de login tras expirar la sesión. Valida el código **y** un marcador de éxito ligero (substring del campo esperado).

## 3. Criterios de aceptación (SLA) fuera del plan
Los SLA de tiempo **no** se validan con Duration Assertion por muestra, sino sobre el agregado de la prueba (percentiles, tasa de error, throughput) con `scripts/analizar_jtl.py`:
```json
{
  "global": { "error_pct_max": 1.0 },
  "transacciones": {
    "01_Login":          { "p95_ms": 800,  "p99_ms": 1500, "error_pct_max": 0.5, "throughput_min": 10 },
    "02_Transferencia":  { "p95_ms": 1200, "p99_ms": 2500, "error_pct_max": 0.1 }
  },
  "regresion": { "p95_tolerancia_pct": 10 }
}
```
- Evalúa las **transacciones** (Transaction Controllers), que es lo que entiende el negocio.
- Excluye la rampa del cálculo si el SLA es de estado estable (`--excluir-inicio 300` segundos).
- `regresion`: falla si el p95 empeora más de X % respecto a una ejecución base (`--base anterior.jtl`).

## 4. APDEX
El dashboard HTML de JMeter calcula APDEX con umbrales `jmeter.reportgenerator.apdex_satisfied_threshold` (500 ms por defecto) y `apdex_tolerated_threshold` (1500 ms), configurables por transacción en `user.properties`. Ajústalos al SLA real.
