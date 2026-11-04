# 03 — Estructura del plan (.jmx)

## Contenido
1. Anatomía del plan
2. Reglas de alcance (scoping) y orden de ejecución
3. Thread Groups
4. Elementos de configuración
5. Controladores lógicos
6. Timers
7. Propiedades vs variables
8. Fragmento XML de referencia

---

## 1. Anatomía

```
Test Plan                                   (variables globales, "Run thread groups consecutively" desactivado)
├── User Defined Variables                  (derivadas de propiedades: host, protocolo...)
├── HTTP Request Defaults                   (protocolo/host/puerto/timeouts desde ${__P()})
├── HTTP Header Manager                     (Content-Type, Accept)
├── HTTP Cookie Manager                     (clear each iteration = true: cada iteración es un usuario nuevo)
├── HTTP Cache Manager                      (simula el navegador; omitir para APIs puras)
├── DNS Cache Manager                       (opcional: balanceadores por DNS)
├── CSV Data Set Config                     (usuarios/datos de prueba)
├── setUp Thread Group                      (opcional: obtener token de servicio, preparar datos)
├── Thread Group / Open Model Thread Group  (carga parametrizada)
│   ├── Transaction Controller "01_Login"
│   │   ├── HTTP Request POST /auth/login
│   │   │   ├── JSON Extractor (token)
│   │   │   └── Response Assertion (código 200)
│   │   └── Uniform Random Timer (think time)
│   ├── Transaction Controller "02_ConsultarSaldo"
│   └── ...
└── tearDown Thread Group                   (opcional: limpieza)
```
Sin listeners de visualización (View Results Tree, Summary Report, gráficas): consumen CPU y memoria en el generador. Los resultados se escriben con `-l resultados.jtl`. En la GUI, para depurar, añádelos **deshabilitados**.

## 2. Alcance y orden

- Un elemento aplica a los samplers de su **mismo nivel e inferiores**. Un HTTP Header Manager hijo de un sampler solo aplica a ese sampler; al nivel del Thread Group aplica a todos.
- Orden de ejecución para cada sampler: Config elements → Pre-processors → **Timers** → Sampler → Post-processors → Assertions → Listeners.
- Consecuencia práctica: **los timers se ejecutan ANTES del sampler** al que aplican. Un timer al nivel del Thread Group retrasa *cada* sampler. Para un think time por paso, pon el timer como hijo del primer sampler del paso (o usa un Flow Control Action con pausa).
- Las aserciones y extractores aplican al sampler padre; si están al nivel de un controlador, aplican a todos los samplers hijos (normalmente no es lo deseado).

## 3. Thread Groups

| Elemento | Núcleo/plugin | Cuándo |
|---|---|---|
| Thread Group | Núcleo | Modelo cerrado: N usuarios, rampa, duración |
| setUp / tearDown Thread Group | Núcleo | Preparación y limpieza |
| **Open Model Thread Group** (5.5+) | Núcleo | Modelo abierto: tasa de llegadas con un *schedule* |
| Concurrency Thread Group | Plugin `jpgc-casutg` | Escalones de concurrencia (estrés), sin calcular rampa manual |
| Ultimate Thread Group | Plugin `jpgc-casutg` | Perfiles arbitrarios (picos) |

Thread Group parametrizado (propiedades verificadas en el código de JMeter):
- `ThreadGroup.num_threads` = `${__P(usuarios,1)}`
- `ThreadGroup.ramp_time` = `${__P(rampa,1)}`
- `ThreadGroup.scheduler` = `true` y `ThreadGroup.duration` = `${__P(duracion,60)}` (segundos), con el Loop Controller en `-1` (infinito) → la duración manda.
- `ThreadGroup.on_sample_error` = `continue` (por defecto). `startnextloop` reinicia la iteración tras un error (útil si un paso fallido invalida los siguientes).

Open Model Thread Group:
- `OpenModelThreadGroup.schedule`, por ejemplo `rate(0/sec) random_arrivals(5 min) rate(${__P(rps,10)}/sec) random_arrivals(${__P(meseta_min,30)} min) rate(${__P(rps,10)}/sec)` (subida lineal en 5 min y luego meseta).
- Funciones del schedule: `rate(N/sec|min|hour)`, `random_arrivals(T)` (llegadas de Poisson), `even_arrivals(T)`, `pause(T)`. Si se omite el `rate` final, se mantiene el inicial.
- API marcada experimental en 5.6: valida el comportamiento en la versión del proyecto.

## 4. Configuración

- **HTTP Request Defaults** (`ConfigTestElement` con GUI `HttpDefaultsGui`): `HTTPSampler.protocol`, `HTTPSampler.domain`, `HTTPSampler.port`, `HTTPSampler.connect_timeout`, `HTTPSampler.response_timeout`. Así los samplers solo llevan método y ruta.
- **Timeouts siempre definidos** (p. ej. 5 000 ms de conexión, 30 000 ms de respuesta): sin ellos, un servidor colgado bloquea hilos indefinidamente y la prueba no termina.
- **Cookie Manager**: `CookieManager.clearEachIteration=true` para simular usuarios nuevos por iteración.
- **CSV Data Set Config**: ver 04.
- **Implementación HTTP**: `HttpClient4` (por defecto). Reutilización de conexiones: `HTTPSampler.use_keepalive=true`. Para simular usuarios nuevos que abren conexión por iteración: `httpclient.reset_state_on_thread_group_iteration=true` (por defecto en 5.x).

## 5. Controladores

| Controlador | Uso |
|---|---|
| **Transaction Controller** | Agrupa los requests de un paso de negocio; su tiempo es la métrica que importa al negocio. `TransactionController.parent=false` para registrar también los hijos; `TransactionController.includeTimers=false` para **excluir** el think time de la medición |
| Throughput Controller | Mezcla de flujos por porcentaje en un mismo Thread Group |
| If Controller | Ramas condicionales; usar `${__jexl3(...)}` o `${__groovy(...)}` con "Interpret condition as variable expression" |
| Once Only Controller | Login una vez por hilo |
| Loop / While / ForEach | Repeticiones y recorrido de resultados extraídos |
| Module / Include Controller, Test Fragment | Reutilizar flujos entre planes |

Mezcla de flujos: o **un Thread Group por flujo** con su propia carga (más claro y medible), o un Thread Group con Throughput Controllers por porcentaje.

## 6. Timers

| Timer | Uso |
|---|---|
| Uniform Random Timer | Think time: retraso constante + aleatorio uniforme |
| Gaussian Random Timer | Think time con distribución normal |
| Constant Timer | Pausa fija (rara vez realista) |
| Constant Throughput Timer | Limita a N muestras/min (por hilo o compartido) |
| **Precise Throughput Timer** | Ritmo objetivo con llegadas de Poisson, más preciso que el anterior |
| Synchronizing Timer | Picos sincronizados (N hilos liberados a la vez) |

## 7. Propiedades vs variables

| | Propiedades `${__P(x)}` | Variables `${x}` |
|---|---|---|
| Alcance | Globales (todos los hilos) | Por hilo |
| Origen | `-J`, `-q`, `user.properties` | User Defined Variables, extractores, CSV |
| Uso típico | Configuración de la prueba (host, carga) | Datos de cada usuario (token, id) |

Patrón: `User Defined Variables` con `host=${__P(host,localhost)}` y luego `${host}` en los elementos (legible y con valor por defecto).

## 8. XML de referencia

Fragmento de HTTP Request verificado contra las plantillas oficiales de JMeter 5.6.3:
```xml
<HTTPSamplerProxy guiclass="HttpTestSampleGui" testclass="HTTPSamplerProxy" testname="POST /api/transferencias" enabled="true">
  <boolProp name="HTTPSampler.postBodyRaw">true</boolProp>
  <elementProp name="HTTPsampler.Arguments" elementType="Arguments">
    <collectionProp name="Arguments.arguments">
      <elementProp name="" elementType="HTTPArgument">
        <boolProp name="HTTPArgument.always_encode">false</boolProp>
        <stringProp name="Argument.value">{"cuentaDestino":"${cuentaDestino}","monto":${monto}}</stringProp>
        <stringProp name="Argument.metadata">=</stringProp>
      </elementProp>
    </collectionProp>
  </elementProp>
  <stringProp name="HTTPSampler.path">/api/transferencias</stringProp>
  <stringProp name="HTTPSampler.method">POST</stringProp>
  <boolProp name="HTTPSampler.follow_redirects">true</boolProp>
  <boolProp name="HTTPSampler.use_keepalive">true</boolProp>
</HTTPSamplerProxy>
<hashTree/>
```
Recuerda: cada elemento va seguido de su `<hashTree>` (con los hijos dentro o vacío). Ojo con la mayúscula de `HTTPsampler.Arguments` (minúscula la "s"): es el nombre real.
