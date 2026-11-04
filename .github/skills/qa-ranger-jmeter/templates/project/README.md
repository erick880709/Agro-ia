# __NOMBRE__ — pruebas de rendimiento (JMeter 5.6.3)

```bash
export CLAVE_PRUEBAS=...                      # nunca en el repositorio
./ejecutar.sh local -Jusuarios=1 -Jduracion=60   # 1) validar el script: 0 % de errores
./ejecutar.sh qa                              # 2) carga definida en env/qa.properties
./ejecutar.sh qa -Jusuarios=100 -Jrampa=600   # sobrescribir parámetros
```
Cada ejecución deja en `resultados/<fecha>-<ambiente>/`: `resultados.jtl`, `reporte/index.html` (dashboard), `resumen.md` (veredicto SLA) y `junit-sla.xml` (CI).
Para comparar contra una referencia aprobada: copiar un `resultados.jtl` revisado a `base/<ambiente>.jtl`.

| Archivo | Para |
|---|---|
| `plan.jmx` | Flujo: 01_Login → 02_ConsultarSaldo → 03_Transferir → 04_ConsultarTransferencia (adaptar a tu sistema) |
| `env/*.properties` | Host, carga, think time y timeouts por ambiente |
| `datos/usuarios.csv` | Datos de prueba (sin contraseñas) |
| `sla.json` | Criterios de aceptación por transacción y tolerancia de regresión |
| `Linea_Base___NOMBRE__.md` | Memoria del proyecto: modelo de carga, SLA, resultados de referencia |
