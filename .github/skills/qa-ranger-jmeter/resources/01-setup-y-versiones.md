# 01 — Setup y versiones

## Contenido
1. Versiones
2. Instalación
3. Memoria del generador (heap)
4. Propiedades: jerarquía y archivos por ambiente
5. Plugins
6. Red corporativa
7. JMeter 6.0 (en desarrollo)

---

## 1. Versiones

| Versión | Estado | Java | Notas |
|---|---|---|---|
| 5.6.3 | **Estable vigente** | 8+ (recomendado 17 o 21) | Open Model Thread Group (5.5+, API experimental) |
| 6.0.0 | En desarrollo (rama `master`) | **17+ obligatorio** | Ver §7 |

Comprueba la versión instalada con `jmeter -v`. JMeter DSL (Abstracta) vigente: 2.2.1 (ver 09).

## 2. Instalación

```bash
# Descargar el binario oficial desde https://jmeter.apache.org/download_jmeter.cgi y verificar su firma/SHA-512
tar xzf apache-jmeter-5.6.3.tgz
export JMETER_HOME=$PWD/apache-jmeter-5.6.3
export PATH=$JMETER_HOME/bin:$PATH
jmeter -v
```
- Windows: `jmeter.bat`; sin GUI: `jmeter -n ...` igual.
- Docker: no hay imagen oficial de Apache; usa una imagen mantenida por tu organización (base Temurin 17 + binario verificado) o `justb4/jmeter`, `alpine/jmeter`, fijando la etiqueta exacta.
- **La GUI es solo para construir y depurar.** Las pruebas de carga se ejecutan **siempre** en modo CLI (`-n`).

## 3. Memoria del generador

Por defecto JMeter arranca con `-Xms1g -Xmx1g`. Para pruebas medianas y grandes:
```bash
export HEAP="-Xms2g -Xmx4g -XX:MaxMetaspaceSize=256m"     # el script bin/jmeter respeta HEAP
export JVM_ARGS="-Djava.net.preferIPv4Stack=true"
```
Reglas: `Xms` = `Xmx` en servidores dedicados; no más del 70–80 % de la RAM física. Ver 12 para síntomas de falta de memoria.

## 4. Propiedades

Jerarquía (la última gana): `bin/jmeter.properties` → `bin/user.properties` → `-p`/`-q archivo.properties` → `-J`/`-G` en la línea de comandos.

**Patrón recomendado**: un archivo por ambiente, versionado (sin secretos), y lo variable por `-J`:
```properties
# env/qa.properties
host=api-qa.ejemplo.com
protocolo=https
puerto=443
usuarios=50
rampa=300
duracion=1800
```
```bash
jmeter -n -t plan.jmx -q env/qa.properties -Jusuarios=100 -l resultados.jtl
```
En el `.jmx`: `${__P(host,localhost)}`, `${__P(usuarios,1)}` (siempre con valor por defecto seguro: 1 usuario).

Opciones CLI verificadas en el código de JMeter 5.6.3: `-n` sin GUI, `-t` plan, `-l` resultados, `-j` log, `-p` archivo de propiedades principal, `-q` archivo adicional, `-J`/`-G`/`-D` propiedades JMeter/globales/sistema, `-L` nivel de log, `-e` reporte al final, `-o` carpeta del reporte, `-g` reporte desde un `.jtl` existente, `-f` borrar resultados/reporte previos, `-r`/`-R`/`-X` distribuido, `-H`/`-P`/`-N`/`-u`/`-a` proxy, `-v` versión.

Secretos: `-Jclave=$CLAVE` desde una variable del pipeline, o `${__env(CLAVE)}` con el plugin de funciones; nunca en archivos versionados.

## 5. Plugins

Instala el **Plugins Manager** (`jmeter-plugins-manager.jar` en `lib/ext/`) y fija versiones con `PluginsManagerCMD.sh install jpgc-casutg=2.10,...`. Plugins frecuentes:

| Plugin | Para |
|---|---|
| Custom Thread Groups (`jpgc-casutg`) | Concurrency Thread Group, Ultimate Thread Group, Arrivals |
| Throughput Shaping Timer (`jpgc-tst`) | Perfil de RPS exacto |
| PerfMon (`jpgc-perfmon`) | Métricas de servidor (preferir APM/Prometheus) |
| WebSocket Samplers, gRPC, Kafka (`di-kafkameter`) | Protocolos (ver 11) |

Cada plugin es una dependencia: registra nombre y versión en la Línea Base e instálalos igual en todos los generadores. Desde 5.5, el **Open Model Thread Group** del núcleo cubre muchos casos para los que antes se usaban plugins de arribos (ver 03).

## 6. Red corporativa

- Proxy de salida: `jmeter -H proxy.corp -P 8080 -N "*.corp.local"` (y `-u`/`-a` si requiere autenticación).
- Certificados internos: importar la CA en el truststore del JDK o usar `-Djavax.net.ssl.trustStore=...`.
- mTLS: Keystore Configuration + `-Djavax.net.ssl.keyStore=... -Djavax.net.ssl.keyStorePassword=...`.
- Plugins sin internet: preinstalar en la imagen del generador.

## 7. JMeter 6.0 (en desarrollo)

Según `xdocs/changes.xml` de la rama `master`:
- **Requiere Java 17** o superior.
- **Elimina** el MongoDB Script Sampler y MongoDB Source Config (los planes que los usen no cargan): migrar a JSR223 + driver propio.
- Actualiza Groovy a 5.x y Saxon-HE a 13.x (revisar scripts JSR223 y XPath2 al actualizar).
- La clase del driver MySQL pasa a `com.mysql.cj.jdbc.Driver`.

Hasta que se publique, usa 5.6.3 y prepara la migración: Java 17 en los generadores, sin BeanShell ni MongoDB.
