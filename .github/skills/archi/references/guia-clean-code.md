# Guía: Clean Code y calidad interna verificable

Usa esta guía para definir y revisar prácticas de código en `14.xx`, consolidarlas en `19-Dimensiones-Arquitectonicas.md` y auditarlas en `25`. Clean Code no se valida por estilo subjetivo ni por límites universales de líneas: exige reglas acordadas, automatización y evidencia.

## Contenido

1. Alcance y ownership
2. Reglas `CC-xxx`
3. Matriz obligatoria
4. Aplicación por contenedor
5. Validación por escenario
6. Criterios de evaluación
7. Gate de cierre

## 1. Alcance y ownership

- `19` es dueño del estándar transversal, herramientas, umbrales y excepciones.
- Cada `14.xx` explica cómo aplica las reglas al lenguaje, framework y riesgo de su `CT-xx`.
- `25` revisa evidencia y no confunde documentación con cumplimiento.
- `18` registra un patrón de diseño solo cuando sea arquitectónicamente significativo; Clean Code no convierte cada práctica local en `TP-xxx`.

Usa IDs estables `CC-001`, `CC-002`, etc. No inventes umbrales de complejidad, cobertura, duplicación o tamaño: usa los acordados por el proyecto o `Missing evidence` con responsable y plan.

## 2. Reglas `CC-xxx`

Define como mínimo estas familias y adapta sus controles al stack:

| ID base | Familia | Regla verificable |
|---|---|---|
| `CC-001` | Nombres y lenguaje | Nombres expresan intención y lenguaje del dominio; abreviaturas y términos tienen definición única. |
| `CC-002` | Cohesión y responsabilidad | Funciones, clases y módulos agrupan una razón de cambio; responsabilidades mezcladas se identifican y corrigen/aceptan. |
| `CC-003` | Dependencias y acoplamiento | Dependencias son explícitas, siguen la dirección arquitectónica y no crean ciclos prohibidos. |
| `CC-004` | Complejidad y flujo | Complejidad, anidamiento y tamaño se controlan con reglas del proyecto; excepciones se justifican. |
| `CC-005` | Errores y cancelación | Errores conservan contexto, no se silencian y respetan timeout/cancelación/transacción. |
| `CC-006` | Estado y efectos | Mutación, I/O, tiempo y aleatoriedad son visibles/controlables; invariantes se protegen. |
| `CC-007` | Duplicación y abstracción | Se elimina duplicación de conocimiento estable sin crear abstracciones especulativas. |
| `CC-008` | Comentarios y documentación | Comentarios explican por qué, riesgo o restricción; no compensan nombres/confusión ni contradicen código. |
| `CC-009` | Pruebas | Pruebas son determinísticas, legibles, aisladas y cubren comportamiento/riesgos, no solo líneas. |
| `CC-010` | Seguridad y observabilidad | No hay secretos ni PII en código/logs; logs son útiles, estructurados y correlacionables sin filtrar datos. |
| `CC-011` | Automatización | Formato, lint, análisis, dependencias y pruebas tienen una expectativa de automatización y condición de aceptación; Vulcano define stages, herramientas y política operativa de fallo. |
| `CC-012` | Revisión y deuda | Cambios críticos tienen revisión; excepciones/deuda poseen owner, razón y fecha/condición de retiro. |

Aplica SOLID, DRY, KISS o YAGNI como heurísticas, no como sellos. Registra el problema y evidencia concreta; no declares incumplimiento solo por preferencia personal.

## 3. Matriz obligatoria

Incluye en `19`:

```markdown
### Clean Code y calidad interna
| `CC-xxx` | Regla | Aplica a | Automatización | Métrica/Umbral | Evidencia de definición | Evidencia de ejecución | Responsable | Estado/Excepción |
|---|---|---|---|---|---|---|---|---|
| CC-003 | Sin ciclos entre módulos de dominio | CT-01, CT-02 | Regla de arquitectura en CI | [acordado] | Regla, alcance y criterio aprobados | [reporte/enlace o Pendiente de implementación] | Equipo backend | Definida |
```

Estados: `Definida`, `Aplicada`, `Validada`, `No cumple`, `No aplica`. `Validada` exige salida de herramienta, revisión o prueba reproducible; `No aplica` exige motivo.

- **Evidencia de definición** demuestra que existen regla, alcance, capacidad de automatización esperada, condición de aceptación y responsable. Puede citar una herramienta corporativa obligatoria o ya observada, pero no diseña el pipeline. Permite cerrar un TO-BE preimplementación en `Definida` sin afirmar cumplimiento del código.
- **Evidencia de ejecución** demuestra que la regla se aplicó o validó mediante código, configuración, revisión, prueba, reporte o pipeline reproducible. Es obligatoria para `Aplicada` y `Validada`.
- En Caso C escribe el estado como `AS-IS: <estado> → TO-BE: <estado>` y enlaza por separado evidencia actual y acción objetivo. En Caso A usa `AS-IS: No aplica → TO-BE: Definida`; en Caso B usa solo el estado AS-IS y `TO-BE: No aplica — auditoría sin rediseño`.

## 4. Aplicación por contenedor

Cada `14.xx` de contenedor con código incluye `### Diseño de código, patrones y Clean Code` con:

1. lenguaje, framework, módulos/paquetes y dirección de dependencias;
2. patrones de diseño aplicados y problema real que resuelven;
3. reglas `CC-xxx` aplicables y excepciones;
4. estrategia de errores, cancelación, transacciones, estado y efectos;
5. herramientas y configuración ya observadas o, en TO-BE, capacidades de formato/lint/análisis/pruebas que deben automatizarse;
6. evidencia AS-IS o criterios de aceptación TO-BE;
7. deuda y acciones con responsable.

No documentes clases o métodos triviales. Usa C4 Nivel 4 o diagrama de paquetes solo si dependencias, patrones o deuda crítica no se entienden mediante tabla/texto.

## 5. Validación por escenario

- **Caso A — Greenfield:** define reglas, capacidades de automatización y criterios; usa `Definida`. Deja a Vulcano herramientas, stages y gates operativos. No marques `Aplicada/Validada` antes de contar con código y evidencia.
- **Caso B — AS-IS:** inspecciona configuración real, ejecuta verificaciones seguras disponibles y cita archivo/comando/reporte. Ausencia de configuración es evidencia de falta, no permiso para inventarla.
- **Caso C — TO-BE:** usa el formato `AS-IS: <estado> → TO-BE: <estado>`, separa ambas evidencias y registra acciones de migración; conserva deuda aceptada en `21`/`24`.

No modifiques código para obtener evidencia durante una solicitud de documentación/auditoría. Ejecuta herramientas que ya existan cuando sean seguras y proporcionales; si requieren instalación, cambios o tiempo material, registra el comando propuesto y `Missing evidence`.

## 6. Criterios de evaluación

| Dimensión | Evidencia preferida | No aceptar como evidencia suficiente |
|---|---|---|
| Nombres/dominio | revisión de símbolos críticos y glosario | opinión sin ejemplos |
| Cohesión/acoplamiento | grafo de dependencias, ciclos, ownership y cambios conjuntos | número de clases aislado |
| Complejidad | reporte de herramienta con umbral acordado y hotspots | límite universal no acordado |
| Duplicación | reporte y análisis de conocimiento duplicado | coincidencia textual sin contexto |
| Pruebas | ejecución, estabilidad, mutación/contratos/riesgos cuando aplique | cobertura porcentual por sí sola |
| Errores | pruebas/rutas de fallo, logs y propagación | `try/catch` contado mecánicamente |
| Seguridad | requisito `SEC-xxx`, revisión de logging y, en AS-IS, reportes observables | “usa buenas prácticas” |
| Automatización | capacidad/criterio definido; en AS-IS, pipeline/configuración y resultado | intención sin condición de aceptación |

Para hallazgos registra ubicación, severidad, regla `CC-xxx`, impacto, corrección/aceptación, owner y evidencia de cierre.

### Frontera con Vulcano

`archi` conserva las reglas de calidad interna y sus criterios por `CT-xx`. Vulcano consume esas
reglas y los `SEC-xxx` de `19.1` para definir herramientas, stages, severidades de bloqueo,
excepciones operativas, SLA de remediación y evidencia continua en CI/CD. No dupliques esa
estrategia dentro de `19` o `14.xx`; enlázala cuando ya exista.

## 7. Gate de cierre

No cierres Clean Code como `Validado` si:

- hay hallazgos críticos/altos abiertos sin aceptación explícita;
- faltan reglas para contenedores con código significativo;
- métricas o umbrales fueron inventados;
- se afirma cumplimiento sin evidencia;
- excepciones carecen de owner y condición de retiro;
- patrones de diseño agregan complejidad sin problema recurrente demostrado.
