# Estimación de Horas para Desarrollo en Spec-Driven Development (SDD)

*Guía de referencia · Equipo de desarrollo*

*Framework de estimación para squads que desarrollan con especificaciones formales y asistencia de agentes de IA.*

> *Nota de fuentes: esta guía combina técnicas de estimación estándar de la industria (COCOMO II, Function Points, PERT/estimación de tres puntos) con un enfoque de calibración basado en datos históricos, adaptado al flujo de trabajo de SDD. La evidencia empírica disponible está resumida en `references/evidencia-benchmarks.md`.*

## Contenido

- 1\. Propósito y alcance

- 2\. Qué es Spec-Driven Development y por qué cambia la estimación

- 3\. Fases del flujo SDD y su impacto en el esfuerzo

- 4\. Principios de estimación

- 5\. Técnicas de estimación recomendadas

- 6\. El factor de aceleración SDD

- 7\. Plantilla de estimación

- 8\. Ejemplo resuelto

- 9\. Roles y categorías de horas

- 10\. Calibración continua del modelo

- 11\. Errores comunes al estimar en SDD

- 12\. Checklist antes de estimar

- 13\. Fuentes y limitaciones de esta guía

## 1. Propósito y alcance

Esta guía es la referencia oficial del equipo para estimar horas de desarrollo cuando el trabajo sigue un flujo de Spec-Driven Development (SDD): se define primero una especificación formal y verificable, y a partir de ella se genera, valida y ajusta el código — con apoyo de agentes de IA en una o más fases.

El objetivo es que dos personas distintas, estimando la misma historia con esta guía, lleguen a números comparables (no idénticos, pero dentro de un rango razonable), y que el equipo pueda calibrar sus estimaciones con datos reales a lo largo del tiempo en lugar de depender solo de la intuición individual.

### 1.1 Cuándo usar esta guía

- Estimación de historias de usuario, tareas técnicas o épicas que se implementarán bajo un flujo SDD (spec → generación asistida → validación → integración).

- Planeación de sprint o de release cuando el equipo necesita convertir complejidad/alcance en horas-persona.

- Retrospectivas de estimación: comparar horas estimadas vs. reales para recalibrar los factores de este documento.

### 1.2 Cuándo NO aplica directamente

- Trabajo puramente exploratorio o de investigación sin especificación previa (spikes) — usar estimación por time-boxing, no esta guía.

- Mantenimiento correctivo urgente (hotfixes) sin ciclo de spec — estimar con la tabla de roles (sección 9) pero sin aplicar el factor SDD.

## 2. Qué es Spec-Driven Development y por qué cambia la estimación

En Spec-Driven Development, la especificación (spec) —no el código— es el artefacto central del que se deriva el trabajo. La spec describe comportamiento esperado, contratos de interfaz, criterios de aceptación y restricciones no funcionales con suficiente precisión para que un agente de IA (o una persona) pueda generar una implementación verificable contra ella.

Esto cambia dónde se concentra el esfuerzo respecto al desarrollo tradicional: baja el tiempo de escritura manual de código boilerplate, pero sube el tiempo de definición de la spec, de revisión crítica del código generado, y de validación de que la implementación cumple exactamente lo especificado — incluyendo casos borde que la IA pudo pasar por alto o "alucinar".

> *Implicación clave para estimar: en SDD, subestimar las fases de especificación y de revisión/validación es el error más común. La generación de código asistida por IA reduce tiempo, pero no elimina las fases de pensamiento crítico — las desplaza.*

## 3. Fases del flujo SDD y su impacto en el esfuerzo

Toda estimación en esta guía se construye por fase, no como un número único. Esto permite ver dónde realmente se concentran las horas y dónde la IA aporta más o menos aceleración.

| **Fase**                        | **Descripción**                                                                                                  | **¿Dónde ayuda la IA?**                                                                                      |
|---------------------------------|------------------------------------------------------------------------------------------------------------------|--------------------------------------------------------------------------------------------------------------|
| 1\. Especificación              | Redactar la spec: comportamiento, contratos, criterios de aceptación, casos borde, restricciones no funcionales. | Poco — requiere criterio humano del dominio. La IA puede ayudar a estructurar, no a decidir qué especificar. |
| 2\. Revisión de spec            | Validar con stakeholders/arquitectura que la spec es completa, consistente y verificable.                        | Bajo — es una actividad de juicio humano.                                                                    |
| 3\. Generación asistida         | El agente de IA genera la implementación (o un borrador sólido) a partir de la spec.                             | Alto — esta es la fase que más se acelera.                                                                   |
| 4\. Revisión de código generado | Lectura crítica del código: ¿es correcto, idiomático, seguro, mantenible? ¿Alucinó algo?                         | Bajo/Medio — la IA ayuda a resumir cambios, pero la revisión crítica es humana.                              |
| 5\. Validación contra spec      | Pruebas (unitarias, integración, contrato) que verifican que la implementación cumple la spec.                   | Medio/Alto — la IA puede generar casos de prueba a partir de la spec.                                        |
| 6\. Integración y ajuste fino   | Integrar con el resto del sistema, resolver conflictos, ajustar detalles que la spec no cubrió.                  | Bajo — suele ser trabajo de contexto amplio del sistema.                                                     |

## 4. Principios de estimación

- Estimar por fase (sección 3), no un número global — así se identifica dónde aplica o no el factor de aceleración por IA.

- Usar rango (optimista / probable / pesimista), no un solo número — la variabilidad en SDD suele ser mayor en la fase de especificación y en la de revisión, no en la de generación.

- Calibrar con datos reales del equipo, no con benchmarks genéricos de la industria — el factor de aceleración por IA depende del stack, la madurez del equipo con el agente, y el dominio.

- Re-estimar cuando la spec cambia — un cambio de spec después de generar código casi siempre cuesta más que el cambio equivalente antes de generar, porque hay que revalidar lo ya generado.

## 5. Técnicas de estimación recomendadas

### 5.1 Línea base histórica calibrada (enfoque de calibración por datos)

Es la técnica primaria de esta guía. En lugar de estimar horas desde cero cada vez, se parte de una línea base histórica: horas reales que tareas similares tomaron en el pasado, agrupadas por tipo de tarea y nivel de complejidad. A esa línea base se le aplica el factor de aceleración SDD (sección 6), que también se recalibra con datos reales (sección 10).

Este es el mismo principio que subyace a los modelos de estimación de costos basados en IA/redes neuronales: en vez de una fórmula fija, se aprende un factor de corrección a partir de proyectos históricos (variables de entrada: complejidad, tamaño, tipo de tarea, experiencia del equipo; salida: horas reales). La diferencia es que aquí el "modelo" es una tabla de factores mantenida por el equipo, actualizable en cada retrospectiva, no una red entrenada — mismo principio, menor costo de implementación, igual de válido para un equipo que aún no tiene volumen de datos para entrenar un modelo estadístico formal.

### 5.2 Estimación de tres puntos (PERT)

Para cada fase (sección 3), estimar tres escenarios y calcular el estimado ponderado:

**E = (O + 4M + P) / 6**

> *v2: para el total de la propuesta, el script usa una distribución log-normal (P5/P95 según el cono de incertidumbre) y entrega el P80 como cifra comprometida — ver `guia-calibracion-y-confianza.md`. La fórmula PERT clásica sigue siendo válida para estimar fases individuales.*

- O (optimista): todo sale bien, sin bloqueos ni retrabajos.

- M (más probable): el escenario esperado con la fricción normal del equipo.

- P (pesimista): la spec tenía huecos, el código generado necesitó reescritura significativa, o aparecieron dependencias no previstas.

> *En SDD, la brecha entre O y P suele ser mayor en la fase de especificación (una spec ambigua puede duplicar el tiempo de las fases siguientes) — vale la pena ser generoso con el escenario pesimista ahí.*

### 5.3 Rúbrica de complejidad

Clasificar cada historia/tarea en un nivel de complejidad antes de estimar horas. Esta clasificación alimenta tanto la línea base histórica (5.1) como el factor de aceleración SDD (sección 6).

| **Nivel** | **Criterios**                                                                                                                                                                       | **Ejemplo típico**                                                                          |
|-----------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|---------------------------------------------------------------------------------------------|
| Baja      | Lógica de negocio simple, sin ambigüedad, contratos ya conocidos por el equipo, sin nuevas integraciones.                                                                           | CRUD estándar, endpoint que sigue un patrón ya existente en el sistema.                     |
| Media     | Lógica de negocio con reglas moderadas, 1-2 integraciones conocidas, algo de ambigüedad resoluble en la revisión de spec.                                                           | Nuevo caso de uso que orquesta 2-3 servicios existentes.                                    |
| Alta      | Lógica de negocio compleja o crítica (ej. cálculo financiero, reglas regulatorias), integraciones nuevas o con sistemas externos, alta necesidad de casos borde bien especificados. | Nuevo módulo de detección de fraude, saga con compensaciones, migración de modelo de datos. |

### 5.4 Function Points / COCOMO II como validación cruzada

Para épicas grandes (varios sprints), es útil validar la estimación bottom-up (por historia) contra una estimación top-down con Function Points o COCOMO II, y entender la diferencia si es mayor al 20%. Estas técnicas no sustituyen las anteriores en SDD — sirven como sanity check para detectar subestimaciones sistemáticas, especialmente en la fase de integración, que estas fórmulas capturan mejor que la estimación historia por historia.

## 6. El factor de aceleración SDD

El factor de aceleración es el multiplicador que se aplica a la línea base histórica (horas que tomaría la tarea sin asistencia de IA) para obtener la estimación bajo el flujo SDD. Un factor de 0.6 significa "60% del tiempo histórico"; un factor de 1.1 significa que la fase toma más tiempo que antes (esto ocurre en especificación y revisión, no es un error).

| **Tipo de tarea**                 | **Especificación** | **Generación** | **Revisión + Validación** |
|-----------------------------------|--------------------|----------------|---------------------------|
| Boilerplate / CRUD estándar       | 0.8×               | 0.3×           | 0.7×                      |
| Lógica de negocio media           | 1.0×               | 0.5×           | 0.9×                      |
| Lógica crítica / regulatoria      | 1.2×               | 0.7×           | 1.1×                      |
| Integración con sistemas externos | 1.1×               | 0.8×           | 1.0×                      |
| Refactor guiado por spec          | 0.9×               | 0.4×           | 0.8×                      |

> *Estos multiplicadores son valores de partida razonables para un equipo que empieza a calibrar — no son verdad universal. Deben ajustarse con los datos reales del propio equipo (sección 10) tan pronto como existan 8-10 tareas completadas de cada tipo.*

### 6.1 Reglas de aplicación (v2)

Con el reparto de fases por defecto (17/9/26/17/17/13), la tabla anterior produce estos ahorros **sobre horas de desarrollo**:

| Tipo de tarea | Horas resultantes | Ahorro sobre desarrollo |
|---|---:|---:|
| Boilerplate / CRUD estándar | 67,2% | 32,8% |
| Refactor guiado por spec | 74,9% | 25,1% |
| Lógica de negocio media | 82,6% | 17,4% |
| Integración con sistemas externos | 95,5% | 4,5% |
| Lógica crítica / regulatoria | 98,0% | 2,0% |

1. **El factor SDD se aplica solo a las horas de Desarrollo.** No se aplica a PM, Arquitecto ni UX/UI (la versión 1 de la skill lo aplicaba a las horas de todos los roles, lo que inflaba el ahorro). QA solo se reduce si el equipo tiene datos calibrados de generación de pruebas con IA.
2. **El ahorro decae con el tamaño del ítem** (horas de desarrollo): ≤16 h → 100% del ahorro; ≤40 h → 80%; ≤120 h → 60%; >120 h → 40%. Es una heurística conservadora alineada con la evidencia de METR (la efectividad de los agentes cae con el tamaño de la tarea) y con `progressive-estimation` (efectividad S 0,9 / M 0,5 / L 0,35 / XL 0,3).
3. **Ante el cliente, presenta el ahorro como rango de partida**, no como garantía. Ahorros de 60–70% como los que asumen algunas herramientas no están respaldados por evidencia pública en contextos empresariales.
4. El cálculo lo hace `scripts/calcular_estimacion.py` (campo `tipo_sdd` por ítem: `crud`, `logica_media`, `critica`, `integracion`, `refactor`, `ninguno`).

## 7. Plantilla de estimación

Usar esta estructura de columnas al estimar una historia o tarea. Es la unidad mínima que debe registrarse para poder calibrar el modelo después.

| **Columna**               | **Contenido**                                                             |
|---------------------------|---------------------------------------------------------------------------|
| Historia / Tarea          | Identificador y nombre corto.                                             |
| Tipo de tarea             | Una de las categorías de la sección 6.                                    |
| Complejidad               | Baja / Media / Alta (sección 5.3).                                        |
| Horas base (histórico)    | Promedio histórico del equipo para ese tipo + complejidad, sin IA.        |
| Factor SDD por fase       | Multiplicadores de la sección 6 aplicados a cada fase de la sección 3.    |
| Estimado O / M / P        | Tres escenarios (sección 5.2) ya con el factor SDD aplicado.              |
| Estimado ponderado (PERT) | (O + 4M + P) / 6.                                                         |
| Horas reales              | Se completa al cerrar la tarea — insumo para la calibración (sección 10). |
| Desviación (%)            | (Real − Estimado) / Estimado.                                             |

## 8. Ejemplo resuelto

Historia: "Endpoint para consultar el score de riesgo de un perfil digital, reutilizando el motor de scoring existente." Complejidad: Media. Tipo: Lógica de negocio media.

| **Fase**               | **Horas base** | **Factor SDD** | **Horas ajustadas** |
|------------------------|----------------|----------------|---------------------|
| Especificación         | 4              | 1.0×           | 4                   |
| Revisión de spec       | 2              | —              | 2                   |
| Generación asistida    | 6              | 0.5×           | 3                   |
| Revisión de código     | 4              | 0.9×           | 3.6                 |
| Validación contra spec | 4              | 0.9×           | 3.6                 |
| Integración            | 3              | —              | 3                   |

Total ajustado (más probable): 19.2 horas. Aplicando PERT con un escenario optimista de 15h y pesimista de 28h (la brecha viene principalmente de la fase de especificación, donde un caso borde de scoring no contemplado obligaría a re-generar):

**E = (15 + 4×19.2 + 28) / 6 ≈ 19.9 horas**

## 9. Roles y categorías de horas

No todas las horas de una tarea las hace la misma persona ni al mismo costo. Al planear capacidad de sprint, desagregar por rol:

| **Rol**                  | **Fases donde participa principalmente**                           | **Nota**                                                                       |
|--------------------------|--------------------------------------------------------------------|--------------------------------------------------------------------------------|
| Product Owner / Analista | Especificación, revisión de spec                                   | Dueño de que la spec sea completa y verificable.                               |
| Arquitecto / Tech Lead   | Revisión de spec, revisión de código en tareas de complejidad alta | Su tiempo es el más caro — reservarlo para lo que realmente lo requiere.       |
| Desarrollador Senior     | Generación asistida, revisión de código, integración               | Guía al agente de IA y valida su salida con criterio.                          |
| Desarrollador Junior     | Generación asistida (tareas de baja complejidad), validación       | Buen punto de entrada: la IA reduce la brecha de experiencia en boilerplate.   |
| QA                       | Validación contra spec                                             | Diseña casos a partir de la spec, no del código — evita sesgo de confirmación. |

## 10. Calibración continua del modelo

Los factores de las secciones 5.1 y 6 son un punto de partida, no un resultado final. El equipo debe recalibrarlos periódicamente con datos reales — este es el ciclo de retroalimentación que hace que la estimación mejore con el tiempo en lugar de estancarse.

- Registrar horas reales por fase (no solo el total) en cada tarea cerrada — sin esto no hay calibración posible.

- Cada 2-4 sprints, comparar el factor SDD usado vs. el factor real observado (horas reales / horas base histórico) por tipo de tarea.

- Si la desviación promedio de un tipo de tarea supera ±20% de forma sostenida, actualizar el multiplicador de la tabla de la sección 6.

- Si el volumen de datos lo justifica (equipo grande, muchas tareas similares), considerar migrar de la tabla de factores a un modelo de regresión simple o a las redes neuronales mencionadas en el artículo de referencia — el principio es el mismo, solo cambia la sofisticación del ajuste.

## 11. Errores comunes al estimar en SDD

- Aplicar el factor de aceleración a toda la tarea en lugar de por fase — subestima especificación y revisión, que casi nunca se aceleran tanto como la generación.

- No re-estimar cuando la spec cambia después de haber generado código — el costo de revalidar suele ser mayor que el de la generación original.

- Confundir "el agente generó código rápido" con "la tarea está lista" — faltan revisión y validación contra la spec, que son las fases donde se detectan alucinaciones.

- Usar los multiplicadores de la sección 6 sin calibrarlos con datos propios después de las primeras 8-10 tareas.

- Estimar tareas de lógica crítica/regulatoria con el mismo factor que boilerplate — la revisión humana ahí no se puede comprimir tanto como sugiere la tabla genérica.

## 12. Checklist antes de estimar

- ¿La spec existe y es lo bastante concreta para generar contra ella? Si no, la tarea no está lista para estimarse con esta guía.

- ¿Se clasificó el tipo de tarea (sección 6) y el nivel de complejidad (sección 5.3)?

- ¿Se estimó por fase, no como número único?

- ¿Se usó un rango (O/M/P) y no un solo valor?

- ¿Se registrará el tiempo real por fase al cerrar la tarea, para poder calibrar después?

## 13. Fuentes y limitaciones de esta guía

Esta guía integra: (a) PERT / estimación de tres puntos, técnica estándar de gestión de proyectos; (b) Function Points y COCOMO II, técnicas clásicas de estimación de software; (c) el principio de calibración por datos históricos, que es la base conceptual de los modelos de estimación de costos de software asistidos por IA/redes neuronales referenciados por el equipo, adaptado aquí a una tabla de factores mantenible sin infraestructura de machine learning; y (d) una descomposición de fases propia del flujo Spec-Driven Development.

> *Limitación conocida: no fue posible acceder al artículo específico indicado como referencia (medium.com no está en la lista de dominios permitidos en este entorno). Si el artículo describe una fórmula o variables distintas a las de la sección 5.1, se recomienda actualizar esta sección para reflejarlas exactamente.*
