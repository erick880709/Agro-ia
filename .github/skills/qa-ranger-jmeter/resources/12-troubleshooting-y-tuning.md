# 12 — Troubleshooting y tuning

## 1. ¿El cuello de botella es el generador?
Señales: CPU del generador > 80 %, GC frecuente/largo (`jmeter.log`, `-Xlog:gc`), throughput que no sube al subir hilos mientras el servidor está holgado, `Connect` alto desde el inicio.
Acciones: quitar listeners y scripting pesado, aumentar heap, repartir en más generadores, máquinas más cercanas al sistema (misma región/red).

## 2. Errores y su lectura
| Síntoma | Causa probable | Acción |
|---|---|---|
| `java.lang.OutOfMemoryError` | Listeners guardando respuestas, heap pequeño, `response_data` en el JTL | Sin listeners, más `HEAP`, no guardar respuestas |
| `Non HTTP response code: java.net.SocketException` / `Connection reset` | Servidor/balanceador cerrando conexiones por saturación o límites | Correlacionar con el servidor; revisar keep-alive y límites del balanceador |
| `Non HTTP response code: java.net.BindException: Address already in use` | Agotamiento de puertos efímeros en el generador | Keep-alive, ampliar rango de puertos (`net.ipv4.ip_local_port_range`), `tcp_tw_reuse`, más generadores |
| `Non HTTP response code: org.apache.http.conn.ConnectTimeoutException` | Servidor no acepta conexiones a tiempo | Saturación del servidor o red; revisar el timeout configurado |
| `SocketTimeoutException: Read timed out` | Respuesta más lenta que `response_timeout` | Es un hallazgo: el servidor no responde a tiempo |
| 401/403 a mitad de la prueba | Token/sesión expirados | Renovación de token (11) |
| 4xx desde el inicio | Script, datos o correlación | Volver a 1 usuario y depurar |
| Variables literales `${token}` en las peticiones | Extracción fallida | Default distinguible + aserción (04) |
| Throughput muy por debajo del esperado con servidor holgado | Timers mal ubicados (aplican a cada sampler), Constant Throughput Timer por hilo | Revisar alcance de timers (03 §2) |
| Tiempos excelentes e irreales | Caché, respuestas de error rápidas, datos repetidos | Validar respuestas, variar datos |

## 3. Tuning del generador
```properties
# user.properties
jmeter.save.saveservice.output_format=csv
jmeter.save.saveservice.response_data=false
jmeter.save.saveservice.autoflush=false
summariser.interval=30
httpclient4.time_to_live=60000          # renovar conexiones periódicamente (balanceadores)
```
- Java 17+, `HEAP` adecuado, sin GUI.
- Linux: aumentar `ulimit -n` (descriptores) y el rango de puertos efímeros en pruebas con muchas conexiones.

## 4. Lectura de anomalías en resultados
- **Dientes de sierra en el tiempo de respuesta**: GC del servidor o procesos periódicos.
- **Degradación progresiva en resistencia**: fugas de memoria, pools que no liberan, crecimiento de tablas.
- **Errores solo al final**: datos de prueba agotados o tokens expirados.
- **Picos al inicio**: calentamiento (JIT, cachés frías): excluir la rampa del análisis.
- **Percentiles altos con promedio normal**: una fracción de usuarios sufre (dependencia lenta, reintentos, nodos desbalanceados).
