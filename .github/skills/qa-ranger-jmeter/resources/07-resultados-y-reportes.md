# 07 — Resultados y reportes

## 1. Formato JTL (CSV)
Columnas por defecto en 5.6.3 (`jmeter.save.saveservice.*`):
`timeStamp,elapsed,label,responseCode,responseMessage,threadName,dataType,success,failureMessage,bytes,sentBytes,grpThreads,allThreads,URL,Latency,IdleTime,Connect`

| Columna | Significado |
|---|---|
| `timeStamp` | Inicio de la muestra (epoch ms) |
| `elapsed` | Tiempo total de la muestra (ms) — **la métrica principal** |
| `Latency` | Hasta el primer byte de respuesta |
| `Connect` | Tiempo de conexión (TCP + TLS) |
| `success` | `true`/`false` (incluye aserciones) |
| `allThreads` | Hilos activos en todos los grupos en ese instante |
| `label` | Nombre del sampler o Transaction Controller |

Para análisis distribuido o con nombres de host: `jmeter.save.saveservice.hostname=true`. **No guardes `response_data`** en pruebas de carga (archivos enormes y datos sensibles).

Transaction Controllers con `parent=false` aparecen como una fila más (su `label`) con el tiempo total de los hijos; el `dataType` es vacío y `responseMessage` contiene "Number of samples in transaction".

## 2. Métricas que importan
| Métrica | Interpretación |
|---|---|
| **p90/p95/p99** | Experiencia de la mayoría / de los peores casos. El SLA se expresa en percentiles |
| Promedio | Engañoso con distribuciones sesgadas; nunca como único criterio |
| Throughput (muestras/s) | Capacidad lograda; compárala con la objetivo (¿se alcanzó la carga?) |
| % de errores | Separar por código: 4xx (script/datos) vs 5xx/timeouts (saturación) |
| Máximo | Útil para detectar timeouts; no para SLA |
| Latency vs elapsed | Si elapsed ≫ latency, el tiempo se va en transferir la respuesta |
| Connect | Alto = problemas de red/TLS o falta de keep-alive |

## 3. Dashboard HTML
`-e -o carpeta` o `jmeter -g resultados.jtl -o carpeta`. Contiene APDEX, resumen por transacción, percentiles en el tiempo, throughput vs hilos, códigos de respuesta.
- Ajusta `jmeter.reportgenerator.apdex_satisfied_threshold` / `apdex_tolerated_threshold` al SLA.
- Excluir la rampa: `jmeter.reportgenerator.start_date` / `end_date`, o filtrar con `analizar_jtl.py --excluir-inicio`.
- Filtrar etiquetas: `jmeter.reportgenerator.exporter.html.series_filter` (regex) para ver solo transacciones.

## 4. Análisis automático
```bash
python scripts/analizar_jtl.py resultados.jtl --sla sla.json --excluir-inicio 300 --solo-transacciones --md resumen.md
python scripts/analizar_jtl.py actual.jtl --sla sla.json --base base.jtl     # detecta regresiones
```
Regresión: falla solo si el p95 empeora más del `p95_tolerancia_pct` **y** más de `p95_min_diferencia_ms` (50 ms por defecto). La condición absoluta evita falsas alarmas: con tiempos de 1–2 ms, un milisegundo de ruido es +100 % (caso real encontrado al validar la skill).

Salida: tabla por etiqueta (muestras, % error, p50/p90/p95/p99, máx, throughput), veredicto por criterio, errores agrupados por código, y código de salida 1 si el SLA falla (gate de CI).

## 5. Cómo interpretar (y qué reportar)
0. **Un SLA absoluto no detecta regresiones**: en la validación, una transacción pasó de 1 a 252 ms y siguió cumpliendo su SLA de 1200 ms; solo la comparación con la base la detectó. Usa ambos.
1. **¿Se alcanzó la carga?** Throughput logrado vs objetivo y Ley de Little (02 §3). Si no, el resultado no responde la pregunta.
2. **¿Errores?** Si hay errores funcionales (4xx, aserciones), el script/datos tienen problemas: corrige antes de concluir.
3. **¿Dónde empezó la degradación?** Cruza p95 en el tiempo con hilos activos: el punto de inflexión es la capacidad.
4. **¿Es el servidor o el generador?** Revisa los recursos del generador (12).
5. **Correlaciona con el servidor**: CPU, memoria, GC, pools, base de datos (APM). El JTL dice *qué* pasó; el monitoreo dice *por qué*.
6. Reporta: veredicto por criterio, cuello de botella observado con evidencia, hipótesis de causa, recomendación y siguiente prueba.

## 6. Tiempo real: Backend Listener
Envío de métricas durante la prueba a InfluxDB/Graphite (`BackendListener` con `InfluxdbBackendListenerClient`) y visualización en Grafana. Útil para pruebas largas y para correlacionar en vivo con el monitoreo del servidor. No reemplaza al JTL (percentiles exactos del análisis posterior).
