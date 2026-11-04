# Guía: Estimación de costos de IA/LLM (tokens)

Complementa `references/guia-pricing-cloud.md` — mismo dueño documental (`17.4-Pricing_<Proyecto>.md` y `17.5-Arquitectura_Costos_<Proyecto>.html`), pero para el componente de costo que la guía cloud no cubre: modelos de lenguaje, embeddings y fine-tuning. Aplica siempre que `10.1`/`14.xx`/`19` incluyan un patrón de IA de `references/guia-catalogo-patrones.md` sección 5 con llamadas a un LLM (RAG, Agent Pattern, Tool Calling, Fine-tuning, Routing/Model Gateway, Semantic Cache).

## Principio rector

"Sin modelo elegido" nunca es motivo para dejar la partida sin número. Si `10.1` registra el modelo como `Por decidir`/`Pilotear` (ver `references/guia-arquetipo-solucion.md`), estima un **rango entre 2-3 modelos candidatos** (uno económico, uno intermedio, uno de mayor capacidad) en vez de escribir "No estimable". El rango es la respuesta correcta a la incertidumbre, no una excusa para omitirla.

## Proceso

1. **Inventaría cada capacidad que llama a un LLM** desde `14.xx` (tools/prompts del Agent Pattern, pasos de un pipeline RAG, endpoints de un servicio de generación). No estimes "el costo de IA" como una sola cifra global: cada capacidad tiene su propio patrón de tokens y volumen.
2. **Para cada capacidad, estima tokens de entrada y salida promedio por llamada:**
   - Entrada = prompt de sistema + esquema de herramientas (si es Tool Calling/Agent Pattern, se reenvía en cada turno salvo prompt caching) + contexto/historial + contenido recuperado (RAG).
   - Salida = razonamiento visible + llamada a herramienta (JSON) + respuesta final al usuario.
   - Para razonamiento, consultar la definición oficial de tokens facturados y usar telemetría cuando exista. No imponer un multiplicador universal 3–7×; antes del piloto, declarar escenarios justificados. No contar razonamiento dos veces si ya está incluido en output_tokens.
3. **Estima el volumen mensual de llamadas por capacidad y ambiente** a partir de la volumetría confirmada en `01` o `05`/RNF. Si falta confirmación, registra escenarios como supuestos pendientes en `04`, nunca como datos medidos o confirmados (ej. N vacantes/mes × M candidatos × llamadas por evaluación).
4. **Aplica la fórmula** por capacidad y súmalas:
   ```
   Costo mensual (capacidad) = llamadas/mes × tokens_entrada_prom × precio_entrada/1M
                              + llamadas/mes × tokens_salida_prom  × precio_salida/1M
   Costo total IA/mes = Σ Costo mensual (capacidad) por todas las capacidades
   ```
5. **Busca el precio publicado vigente** de cada modelo candidato con WebSearch/WebFetch (igual que en `guia-pricing-cloud.md` paso 3) — nunca de memoria, los precios de LLM cambian con frecuencia y varían por región/deployment (Global Standard vs. Data Zone vs. PTU).
6. **Modela incertidumbre por ambiente:** escenarios mínimo/esperado/alto de llamadas, turnos, tokens y reintentos. Usa mediciones o supuestos explícitos; no aplicar un buffer obligatorio ×2–3 ni porcentajes universales. Documenta base y factores para evitar doble conteo. Incluye pruebas, evaluaciones, fallback y errores facturables.
7. **Si hay embeddings/RAG**, estima aparte: costo de indexación (una vez, o por lote de ingesta) + costo de embedding por consulta (mucho más económico por token que generación, pero con su propio precio publicado) — no lo mezcles con el costo de generación del LLM principal. El almacenamiento/consulta del vector store ya se cubre en la columna "Base de datos" de `guia-pricing-cloud.md`; aquí solo va el costo de *calcular* el embedding.
8. **Si hay fine-tuning**, sepáralo en dos líneas: costo de entrenamiento (uso único o por reentrenamiento) y costo de hosting/inferencia del modelo afinado (recurrente, a veces con precio por token distinto al modelo base).
9. **Compara capacidad aprovisionada y pago por uso** con tarifas vigentes, unidades, horas, compromiso, utilización y punto de equilibrio calculado. No prometer porcentajes fijos de ahorro ni agregar cargos por tokens ya cubiertos por capacidad; separar overflow si aplica.
10. **Guarda el resultado** dentro de `17.4-Pricing_<Proyecto>.md`, en su propia sección "Estimación de costos de IA/LLM", y alimenta con el mismo número la columna IA/LLM de `17.5` (`references/plantilla-reporte-costos.md`) — no dupliques ni recalcules entre ambos.

## Plantilla de la sección "Estimación de costos de IA/LLM"

```markdown
## Estimación de costos de IA/LLM

**Modelo(s) candidato(s):** [Por decidir — rango entre: económico / intermedio / capacidad alta] o [modelo confirmado].
**Familia:** [chat/instrucción estándar | reasoning — explicar tokens facturados y fuente de estimación].

| Capacidad (`14.xx`/tool) | Volumen/mes | Tokens entrada prom. | Tokens salida prom. | Fuente del volumen |
|---|---:|---:|---:|---|
| [ej. `score_candidate`] | [N llamadas] | [N] | [N] | [ej. "N vacantes/mes × M candidatos, ver `01-Linea-Base`"] |

| Modelo candidato | Precio entrada/1M | Precio salida/1M | Costo mensual base | Costo mensual por escenario | Fuente |
|---|---:|---:|---:|---:|---|
| [ej. económico] | $[x] | $[x] | $[x] | $[x] | [enlace a pricing oficial, fecha de consulta] |
| [ej. intermedio] | $[x] | $[x] | $[x] | $[x] | [enlace] |
| [ej. capacidad alta] | $[x] | $[x] | $[x] | $[x] | [enlace] |

**Rango total estimado:** $[mínimo]–$[máximo]/mes (supuestos de escenarios declarados).

**Supuestos declarados:**
- [Volumen de llamadas y de dónde sale cada número.]
- [Cantidades por escenario, reintentos/contingencia y evidencia o justificación.]
- [Si aplica: costo de embeddings/RAG por separado; costo de fine-tuning por separado; PTU descartado/considerado y por qué.]

**Condición de cierre:** validar el consumo real de tokens durante el primer sprint/fase piloto y comparar contra este rango antes de comprometer un techo de gasto definitivo con Financiera.
```

## Reglas de honestidad

- Nunca presentes un solo número puntual cuando el modelo no está decidido — presenta el rango de al menos 2 candidatos.
- Incluye los tokens de razonamiento que facture el proveedor, sustentados en mediciones o escenarios; un factor supuesto no es consumo observado.
- Si no encuentras el precio publicado de un modelo específico, usa el modelo equivalente más cercano de la misma familia y dilo explícitamente en la columna "Fuente".
- Expresa la incertidumbre mediante escenarios y supuestos calibrables; no ocultar contingencia en la tarifa ni duplicarla en volumen y total.
- Si el proyecto ya tiene un Enterprise Agreement o descuento negociado con el proveedor de IA, pregúntale al usuario antes de asumir precio de lista — igual que en `guia-pricing-cloud.md`.


## Contrato por ambiente y tarifas diferenciadas

Aplicar [contrato-costos.md](contrato-costos.md): `17.4.1` posee las partidas por ambiente y alimenta los bloques numéricos de `17.4`/`17.5`. La plantilla anterior orienta la explicación; los totales se generan desde el manifiesto, sin un segundo cálculo manual.

Distinguir operaciones de negocio, conversaciones, turnos, llamadas al modelo y llamadas a tools. Una tool determinista no factura tokens por sí misma, pero su resultado puede entrar al siguiente turno. Contemplar historial acumulado y tokens de entrada cacheada/no cacheada por separado cuando el proveedor admita esa tarifa y exista una tasa justificable.

Crear meters separados para entrada, caché, salida facturada, embeddings y herramientas facturables (búsqueda, OCR, audio u otras). Usar `unit_size` para la unidad publicada (por ejemplo 1000000 tokens). La indexación inicial y entrenamiento inicial son `one_time`; consultas, ingestas recurrentes y reentrenamientos programados se dimensionan en su periodo correspondiente. No omitir embeddings por considerarlos baratos; el vector store sigue en cloud para evitar duplicarlo.

Cada modelo mutuamente excluyente se cotiza en un manifiesto/reporte separado con sufijo de alternativa. Los escenarios de un manifiesto varían cantidades, no suman modelos candidatos como si se desplegaran simultáneamente. Consultar la modalidad exacta: API directa, proveedor intermediario, región, versión, batch, caché o PTU; no intercambiar sus tarifas.

Si falta volumetría confirmada, los escenarios quedan explícitamente supuestos con pendiente en `04`; no atribuirles evidencia inexistente. Durante piloto/operación conciliar por ambiente tokens facturados, llamadas, caché, reintentos y servicios adicionales con telemetría/factura, registrar periodo y desviación y actualizar cantidades. Un presupuesto estimado no certifica consumo real ni cumplimiento de calidad/latencia del modelo.
