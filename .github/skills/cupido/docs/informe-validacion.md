# Informe de validación — effort-estimator v1 → v2

*Validación contra `Enreign/progressive-estimation`, `kennyth01/jira-ticket-estimator`, `Derek-Jones/Small-teams/Project-22` y `Derek-Jones/Software-estimation-datasets`.*

## 1. Resumen

La v1 tenía una base sólida para preventa (flujo con `epicureo`/`specter`, metodología antes de cronograma, roles con criterios distintos, estimación IA siempre junto a la tradicional, supuestos explícitos). Ninguna de las skills de referencia cubre el contexto comercial (propuesta, vigencia, branding, costo por rol) tan bien como la v1.

Sus debilidades estaban en la **conversión a horas** y en la **incertidumbre**: no tenía modo de Puntos de Función, convertía SP a horas con una tabla fija no calibrada, trataba la jornada como 8 h productivas, usaba rangos simétricos y hacía toda la aritmética dentro del modelo. La v2 corrige esos puntos con evidencia de los datasets.

## 2. Comparativo por dimensión

| Dimensión | v1 | progressive-estimation | jira-ticket-estimator | v2 |
|---|---|---|---|---|
| Contexto preventa (propuesta, costo, vigencia, branding) | Fuerte | No cubre | No cubre | Fuerte |
| Tamaño funcional objetivo (PF) | No existe | No | No | **Modo PF IFPUG/COSMIC** |
| Conversión SP → horas | Tabla fija (≈14 h/SP) | Híbrido SP/horas | Complejidad 1–10 → minutos | **Exige h/SP calibradas** |
| Capacidad diaria | `días × 8` | 8 h | — | **Jornada × factor productivo** |
| Distribución de incertidumbre | PERT simétrico, ±20% | **Log-normal + P80/P90 por tamaño** | Redondeo a buckets | **Log-normal + cono + P80** |
| Cono de incertidumbre | Buffer por "nivel" | **Sí, por fase** | No | **Sí, mapeado a epicureo/specter** |
| Aceleración IA | Por fase, conservadora | Efectividad decae con tamaño | 60–70% ahorro fijo | **Por fase + decaimiento, solo dev** |
| Cálculo determinístico | No (lo hace el LLM) | Fórmulas + tests | **Script Python** | **Script Python + self-test** |
| Calibración | Mención genérica | **PRED(25), log de reales, reglas** | Velocidad | **PRED(25), log, reglas ±20%** |
| Guardas anti-patrón | XL, SP>8 | **5 guardas** | — | **6 guardas en el script** |
| Evals | No | Sí | No | **5 casos** |

## 3. Hallazgos con evidencia

### H1. La conversión fija SP → días no es válida (crítico)
La v1 sumaba 0,5 + 0,6 + 0,3 + 0,15 + 0,2 = 1,75 días/SP ≈ 14 h por SP. En Project-22 (617 historias con horas reales) la mediana es **1,05 h/SP**. Los SP son relativos a cada equipo; una tabla fija puede errar un orden de magnitud. **v2:** el modo SP exige `horas_por_sp` calibradas y, si no existen, se redirige a Modo PF.

### H2. Faltaba el modo de Puntos de Función (crítico para el objetivo del equipo)
La skill no permitía estimar horas a partir de los PF asignados a cada HU, que es la práctica que se quiere institucionalizar. **v2:** nueva guía y modo `pf` con PDR contrastada contra 8 datasets: medianas de **6 a 24 h/PF**; banca 11–15 h/PF; las HU pequeñas tienen PDR más alta (China: 10,5 h/PF en <100 PF vs 4,9 en >1000 PF).

### H3. La jornada se trataba como 100% productiva
`días × 8` ignora reuniones y ceremonias y no usa la jornada real de 8,4 h. **v2:** horas efectivas = jornada × factor productivo (0,75 → 6,3 h), con regla para no descontar dos veces cuando la tasa viene de timesheet completo.

### H4. Rangos simétricos subestiman la cola de sobrecostos
En SiP (12.299 tareas) la mediana real/estimado es 1,0 pero el P80 es **2,0** en tareas ≤4 h y 1,5 en >40 h; en agregado, 1,30. `progressive-estimation` validó con 84k pares que la log-normal ajusta mejor que la beta de PERT en todas las bandas. **v2:** log-normal con P5/P95 por fase del cono; costo sobre P80. Los buffers implícitos (43/23/12/5%) coinciden en orden de magnitud con la tabla de buffers de la v1, que se conserva como control.

### H5. El ahorro por IA se aplicaba a todos los roles
La v1 partía de "las horas por rol" para el cálculo SDD, lo que reduce también PM, arquitectura y UX. **v2:** solo desarrollo, con decaimiento por tamaño. Los ahorros resultantes (2–33% según tipo) son más defendibles que el 60–70% de `jira-ticket-estimator`; METR (2025) incluso midió desarrolladores experimentados 19% más lentos con IA en su contexto.

### H6. Aritmética dentro del modelo → cifras inconsistentes entre formatos
La v1 exigía que MD, HTML y PPTX coincidieran, pero no daba el mecanismo. **v2:** `scripts/calcular_estimacion.py` produce un JSON único; self-test reproduce el ejemplo de la guía top-down (206,8 h) y los ahorros SDD de la guía.

### H7. Branding desalineado con el manual vigente
La guía de branding usaba `0E337C`/`263474` y Arial, y la plantilla bundleada era un deck de DevOps. El Manual de marca (mayo 2025) define Azul Eléctrico `0072BC`, Azul Grafito `132436`, Azul Infinito `0E337C`, Blanco Puro y tipografía Reddit Sans. **v2:** plantilla oficial de 16 slides (optimizada de 42 MB a 7 MB) y guía reescrita con mapeo de layouts, reglas de logo y co-branding.

### H8. Efecto del tamaño del equipo no modelado (recomendación pendiente)
Project-22 muestra que más desarrolladores en una misma historia elevan su costo (`e^(0,3 × personas)`); `progressive-estimation` usa +15% de comunicación por persona adicional. **Pendiente:** agregar un factor de colaboración cuando una HU requiera 2+ desarrolladores simultáneos.

## 4. Lo que la v1 hacía mejor que las referencias (se conserva)
- Integración con el flujo de preventa (`janus → epicureo → specter → effort-estimator → proposal-doc-generator`).
- Paso 0 obligatorio de metodología, con proyección distinta para Scrum/XP/SAFe/Kanban/Cascada.
- Criterios distintos por rol (PM por duración, Arquitecto por complejidad, QA formulado, UX por alcance).
- Estimación IA siempre junto a la tradicional y nunca "gratis".
- Entregables comerciales: vigencia, exclusiones, próximos pasos.

## 5. Recomendaciones siguientes
1. Construir la **PDR propia de PersonalSoft** por stack con las HU cerradas de los squads actuales (meta: 20–30 HU por tecnología).
2. Mantener una **biblioteca de historias de referencia** por tamaño y tipo SDD con horas reales.
3. Medir **PRED(25)** por squad cada 2–3 sprints; objetivo ≥ 65% en 6 meses (SiP, referencia de industria: 45%).
4. Registrar horas reales **con y sin IA** para reemplazar los factores SDD de partida por factores calibrados.
5. Implementar el factor de colaboración (H8) y un conteo asistido de PF desde el frontmatter de `specter`.

## 6. Fuentes
Ver `references/evidencia-benchmarks.md`. Las cifras de terceros deben verificarse antes de citarlas en documentos externos.
