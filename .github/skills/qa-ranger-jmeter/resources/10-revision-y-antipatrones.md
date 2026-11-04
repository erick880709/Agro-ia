# 10 — Revisión de planes y antipatrones

`L` = detectada por `scripts/lint_jmx.py`; `M` = revisión manual.

| # | Antipatrón | Sev. | Det. | Corrección |
|---|---|---|---|---|
| J1 | Propiedad desconocida para el elemento (errata, nombre inventado) | **Bloqueante** | L | Nombre del catálogo verificado (`scripts/data/jmx_catalogo.json`) |
| J2 | Listener de visualización habilitado (View Results Tree, Summary/Aggregate Report, gráficas) | Mayor | L | Deshabilitar; resultados vía `-l` |
| J3 | BeanShell (sampler, pre/post, aserción, listener) | Mayor | L | JSR223 + Groovy |
| J4 | JSR223 sin caché o con `${var}` dentro del script | Mayor | L | `cacheKey=true`; `vars.get("var")` |
| J5 | JSR223 con lenguaje distinto de Groovy | Menor | L | Groovy |
| J6 | Host/protocolo/puerto literal en samplers | Mayor | L | HTTP Request Defaults con `${__P()}` |
| J7 | Usuarios, rampa o duración literales (no parametrizados) | Mayor | L | `${__P(usuarios,1)}` etc. |
| J8 | Sin timeouts de conexión/respuesta | Mayor | L | `connect_timeout`/`response_timeout` en Defaults |
| J9 | Ningún timer (sin think time ni ritmo) | Mayor | L | Timers de reflexión o de throughput |
| J10 | Thread Group sin duración y con loop infinito, o rampa 0 con muchos hilos | Mayor | L | `scheduler=true` + duración; rampa proporcional |
| J11 | Sampler sin ninguna aserción en su alcance | Mayor | L | Response Assertion (código + marcador) |
| J12 | Extractor sin valor por defecto | Menor | L | Default distinguible (`NO_ENCONTRADO_x`) |
| J13 | Sin Cookie Manager en planes web con sesión | Menor | L | HTTP Cookie Manager |
| J14 | CSV con ruta absoluta | Mayor | L | Ruta relativa o `${__P(datos,...)}` |
| J15 | Secretos literales (password, token, Authorization) | **Bloqueante** | L | `${__P(clave)}` desde el pipeline |
| J16 | Debug Sampler / Debug PostProcessor habilitado | Menor | L | Deshabilitar |
| J17 | Recursos embebidos sin necesidad en pruebas de API | Menor | L | Desactivar `image_parser` |
| J18 | Sin Transaction Controllers (métricas solo por request técnico) | Menor | L | Agrupar por paso de negocio |
| J19 | Duration Assertion como SLA principal | Menor | L | SLA sobre percentiles agregados (05 §3) |
| J20 | Elemento deshabilitado olvidado en el plan | Menor | L (aviso) | Eliminar o documentar |
| J21 | `<hashTree>` desbalanceado / XML inválido | **Bloqueante** | L | Regenerar el elemento |
| J22 | Datos insuficientes para los hilos / datos compartidos entre generadores | Mayor | M | Ver 04 §2 |
| J23 | Modelo de carga sin justificar (hilos "porque sí") | Mayor | M | Ley de Little (02 §3) |
| J24 | Correlación faltante (IDs/tokens literales grabados) | **Bloqueante** | M | Extraer y reutilizar (04 §1) |
| J25 | Uso de elementos de plugins sin declarar | Menor | L | Línea Base + Plugins Manager |

## Checklist
- [ ] `lint_jmx.py` sin bloqueantes ni mayores.
- [ ] 1 usuario/1 iteración con 0 % de errores y respuestas verificadas.
- [ ] Modelo de trabajo y SLA documentados; carga calculada.
- [ ] Datos suficientes y correlación completa.
- [ ] Parametrizado por ambiente; sin secretos.
- [ ] Generador con capacidad verificada.
- [ ] Línea Base actualizada (resultados de referencia).

## Formato
```markdown
## Revisión JMeter — <plan>
Resumen: X bloqueantes, Y mayores, Z menores. <veredicto>
### Bloqueantes
1. **[J1] plan.jmx: "Aserción código" (ResponseAssertion)** — propiedad `Assertion.test_strings` no existe; la real es `Asserion.test_strings` (errata histórica). La aserción se carga vacía y nunca falla.
   Corrección: `<collectionProp name="Asserion.test_strings">...`
...
```
