# Evidencia empírica y benchmarks

Cifras calculadas directamente sobre datasets públicos de estimación (repositorio `Derek-Jones/Software-estimation-datasets` y `Derek-Jones/Small-teams/Project-22`). Úsalas como **punto de partida y para validar cordura**, nunca como sustituto de datos propios del equipo. Son datos de proyectos sin asistencia de IA (pre-2020 en su mayoría).

## 1. Productividad por Punto de Función (PDR, horas/PF, ciclo completo)

| Dataset | n | P25 | Mediana | P75 |
|---|---:|---:|---:|---:|
| Desharnais (Canadá, IFPUG) | 81 | 10,6 | 17,2 | 22,5 |
| China (IFPUG) | 499 | 4,3 | 8,1 | 15,4 |
| Albrecht (IBM) | 24 | 17,9 | 23,7 | 32,0 |
| Kitchenham | 145 | 4,2 | 6,3 | 8,7 |
| Maxwell (banca, Finlandia) | 62 | 7,3 | 10,9 | 19,1 |
| Finnish | 38 | 4,2 | 8,4 | 14,3 |
| Huijgens EBSPM (banca/telco, Países Bajos) | 22 | 6,3 | 20,2 | 85,0 |
| Valdés-Souto (México, COSMIC h/CFP) | 57 | 4,7 | 10,2 | 18,2 |

Lectura práctica:
- Las medianas se concentran entre **6 y 24 h/PF**; el valor por defecto del script (**10 h/PF**) está en la zona central.
- Banca: Maxwell 10,9 h/PF; en Huijgens el subgrupo bancario tiene mediana 14,6 h/PF (n=10).
- **Efecto tamaño** (China): <100 PF → 10,5 h/PF; 100–300 → 9,2; 300–1000 → 6,4; >1000 → 4,9. Las HU sueltas se comportan como proyectos pequeños.
- La dispersión entre P25 y P75 es de 2× a 4×: **por eso la PDR debe calibrarse con datos propios** tras 20–30 HU.

## 2. Story Points → horas (Project-22)

Equipo de 3 personas, 8 meses, 617 historias con SP y horas reales.

- Mediana **1,05 h por SP** (P25 0,70; P75 1,43; P90 1,80). Ajuste log-log: `horas ≈ 0,91 × SP^0,99`.
- En ese equipo "1 SP ≈ 1 hora ideal". En otro equipo, 1 SP puede ser medio día.
- Conclusión: **no existe conversión universal SP → horas**. La tabla fija de la versión 1 de esta skill (1,75 días/SP sumando roles ≈ 14 h/SP) sobreestimaría este equipo ~13×. Modo SP exige `horas_por_sp` calibradas.
- El análisis original de Project-22 encontró que 1 desviación estándar alrededor del modelo equivale a un factor de 1,9× y el 95% a 3,4×; y que el número de desarrolladores en una historia aumenta su costo (`Actual = 0,6 × SP^1,07 × e^(0,3 × personas)`).

## 3. Precisión de estimaciones a nivel de tarea (SiP, 12.299 tareas)

| Tamaño estimado | n | Mediana real/estimado | P80 real/estimado |
|---|---:|---:|---:|
| ≤ 4 h | 7.800 | 1,00 | 2,00 |
| 4–16 h | 2.779 | 1,00 | 1,73 |
| 16–40 h | 1.149 | 0,78 | 1,59 |
| > 40 h | 571 | 0,64 | 1,51 |

- El 38% de las tareas supera su estimado; solo el 45% queda dentro de ±25%.
- En agregado, real/estimado = **1,30** (las sobreestimaciones y subestimaciones no se compensan).
- Implicación: el buffer de 15–40% es razonable para el **total del proyecto**, pero no para comprometer una tarea individual (a nivel tarea el P80 es 1,5×–2×).

## 4. Aceleración por IA — lo que dice (y no dice) la evidencia

- No existe todavía un dataset público grande de horas reales de desarrollo asistido por IA en proyectos empresariales.
- METR (2025, estudio controlado con desarrolladores experimentados de código abierto) reportó que, en ese contexto, los desarrolladores tardaron ~19% **más** con herramientas de IA, aunque creían ir más rápido. Sus datos de agentes autónomos muestran que la tasa de éxito cae fuertemente con el tamaño de la tarea.
- `progressive-estimation` (Enreign) modela esa caída con efectividad del agente S 0,9 / M 0,5 / L 0,35 / XL 0,3.
- `jira-ticket-estimator` (kennyth01) asume ahorros de 60–70% en implementación: optimista frente a la evidencia disponible.
- Los factores SDD de esta skill dan ahorros sobre desarrollo de **2% (lógica crítica) a 33% (CRUD)**: conservadores y más defendibles ante un cliente. Se aplican solo a horas de desarrollo y decaen con el tamaño del ítem.

> Verifica las fuentes antes de citarlas en una propuesta externa: los enlaces y cifras de terceros pueden haber cambiado.

## 5. Fuentes
- Derek M. Jones, *Software-estimation-datasets* (GitHub) y *Small-teams/Project-22* (GitHub).
- Jones & Cullum, análisis del dataset SiP (arXiv 1901.01621).
- METR, estudio de productividad con IA en desarrolladores de código abierto experimentados (2025).
- Enreign, *progressive-estimation* (GitHub) — `docs/deep-validation-findings.md`.
- kennyth01, *jira-ticket-estimator* (GitHub) — `heuristics.json`.
