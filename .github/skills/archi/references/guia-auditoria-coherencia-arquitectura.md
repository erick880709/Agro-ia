# Guía: auditoría de coherencia y cumplimiento arquitectónico

Esta guía convierte `25-Revision-Tecnica-Arquitectura.md` en la auditoría formal de **prometido → diseñado → verificado**, con controles tempranos para evitar descubrir desviaciones al final. No crea otra fuente de verdad: cada compromiso y elemento de diseño conserva su documento dueño.

## Contenido

1. [Principios](#principios)
2. [Checkpoints progresivos](#checkpoints-progresivos)
3. [Estados de evidencia](#estados-de-evidencia)
4. [Estructura obligatoria de la auditoría 25](#estructura-obligatoria-de-la-auditoría-25)
5. [Reglas de cobertura](#reglas-de-cobertura)
6. [Validación automática](#validación-automática)
7. [Reauditoría por cambios](#reauditoría-por-cambios)

## Principios

1. Audita evidencia, no intención. Un enlace prueba existencia; no prueba suficiencia.
2. Revisa en ambas direcciones:
   - todo driver o compromiso aplicable llega a una respuesta de diseño y validación;
   - todo elemento de diseño tiene driver, restricción o decisión que justifique su existencia.
3. Distingue diseño, demostración e implementación. En Greenfield no declares implementación por disponer de diagramas; en AS-IS no declares implementación sin evidencia reproducible.
4. No apruebes por promedio. Un compromiso crítico sin cubrir bloquea aunque la cobertura global sea alta.
5. Registra desviaciones en el artefacto afectado y en `20`/`21`; `25` las audita, no las legaliza.
6. Ejecuta `25` como revisión independiente: no des por válidos los checklists locales sin contrastar evidencia.

## Checkpoints progresivos

Los checkpoints no generan documentos nuevos. Registra el resultado en el último artefacto del checkpoint, con fecha, revisor, estado, hallazgos y artefactos corregidos.

| Checkpoint | Momento | Verificación mínima | Dueño del resultado | Condición de avance |
|---|---|---|---|---|
| `CP-01 Drivers` | Después de `07`/`08` | `OBJ`, restricciones, supuestos, `QA`, `FAS`, 13 atributos y 6 pilares sin contradicciones ni críticos huérfanos | Subsección en `08` y actualización de `02`-`07` | Cero driver crítico sin ID, fuente, prioridad o disposición |
| `CP-02 Selección y viabilidad` | Después de `10`-`13` | Alcance completo asignado, baseline coherente, condiciones de selección, incertidumbres y PoC | `10`, `10.1`, `12` o `13` según aplique | Cero capacidad incluida sin asignación; cero incertidumbre crítica sin decisión |
| `CP-03 Integridad del diseño` | Después de `14`-`17` | `scope → CT → componente/API → DATA/modelo físico aplicable → flujo → despliegue`; madurez, cobertura de persistencia, diccionario físico 1:1, nombres, owners, tecnologías y relaciones consistentes | Subsección en `17`, o en `14` si `17` no aplica | Cero capacidad perdida, operación priorizada en `Propuesta`, persistencia narrativa sin `DATA-xxx`, objeto/campo físico sin documentar, `CT/API/DATA` crítico huérfano o desviación no aprobada |
| `CP-04 Reconciliación` | Después de `20`-`22` o `24` | Tácticas, dimensiones, seguridad, decisiones, riesgos, costos y roadmap reconciliados con el diseño | `20` y hallazgos en `21` | Cero decisión activa contradictoria, riesgo crítico sin disposición o promesa sin respuesta |
| `AUD-25` | Después de completar artefactos técnicos | Auditoría completa, ATAM, matrices y validación automática | `25` | Dictamen `Apto` o `Apto con observaciones`; cero bloqueantes |

Si un checkpoint falla, vuelve al primer artefacto afectado y repite el checkpoint. No esperes a `25` para registrar una inconsistencia conocida.

## Estados de evidencia

Usa estos estados en la matriz de compromisos. No los confundas con el cierre documental `Cumple/No cumple`:

| Estado | Evidencia mínima |
|---|---|
| `Definido` | Compromiso, alcance, criterio y owner explícitos |
| `Diseñado` | Respuesta materializada en vistas, contratos, datos, despliegue, táctica o decisión |
| `Verificado en diseño` | Revisión cruzada y ATAM/análisis demuestran coherencia y suficiencia razonada |
| `Demostrado` | PoC, prueba o evidencia reproducible supera el umbral acordado |
| `Implementado` | Código, configuración, contrato desplegado o IaC verificable |
| `Validado operacionalmente` | Evidencia de ejecución, observabilidad o producción satisface el criterio |
| `Desviado con aprobación` | Desviación explícita, `DA-xxx`, riesgo, aprobador y condición de cierre |
| `No aplica` | Motivo verificable; no se usa para evitar una obligación vigente |

Mínimos por escenario:

- Caso A/C preimplementación: todo compromiso incluido llega al menos a `Diseñado`; los `QA-xx` prioritarios llegan a `Verificado en diseño` y a `Demostrado` cuando una PoC/prueba sea gate.
- Caso B: toda afirmación sobre el estado actual llega al menos a `Implementado`; usa `Validado operacionalmente` solo con evidencia de ejecución.
- Caso C: registra por separado `AS-IS` y `TO-BE`; no presentes el estado objetivo como estado actual.

## Estructura obligatoria de la auditoría 25

### 1. Alcance y snapshot auditado

Declara escenario, fecha, auditor/revisor, commit o versión del proyecto y alcance. Incluye todos los artefactos aplicables `01`-`24` y assets:

```markdown
### Snapshot de artefactos auditados
| Artefacto | Aplicable | Versión/SHA-256 | Estado de cierre | Observaciones |
|---|---|---|---|---|
| 14-Vistas-C4.md | Sí | <hash> | Cumple | — |
```

El hash evita aprobar una combinación de documentos distinta de la revisada.

### 2. Matriz de compromisos arquitectónicos

Incluye cada `OBJ-xx`, restricción aplicable, supuesto crítico, `QA-xx`, `FAS-xxx`, condición de selección, condición de PoC, `SEC-xxx`, riesgo aceptado y compromiso de migración/roadmap.

```markdown
### Matriz de compromisos arquitectónicos
| ID fuente/compromiso | Tipo | Promesa o criterio verificable | Respuesta de diseño | Evidencia/validación | Estado | Desviación/DA | Responsable |
|---|---|---|---|---|---|---|---|
| QA-01 | Calidad | p95 bajo el umbral acordado | CT-02 + TP-004 | 14.02, 18, ATAM | Verificado en diseño | — | Arquitectura |
```

Una fila no puede cerrarse con frases como “se tendrá en cuenta”. La respuesta debe citar IDs y artefactos concretos.
Usa una fila por ID fuente canónico; no agrupes varios `OBJ/QA/FAS/SEC` en una sola fila. Para una condición o compromiso sin ID canónico, conserva su identificador de sesión y artefacto, por ejemplo `C-01@10`.

### 3. Trazabilidad bidireccional del diseño

Incluye cada `ARQ-xxx`, `CT-xx`, `API-xxx`, `DATA-xxx`, `TP-xxx`, tecnología crítica y servicio cloud material. Las operaciones API pueden agruparse por `API-xxx` cuando comparten driver; conserva excepciones críticas por operación. Cada `DATA-xxx` cita su owner, fuente de verdad, `16.xx`, nivel de madurez y esquema físico cuando sea requerido.

```markdown
### Trazabilidad bidireccional de elementos de diseño
| Elemento de diseño | Tipo | Driver/restricción/decisión | Artefacto dueño | Evidencia | Estado |
|---|---|---|---|---|---|
| CT-02 | Contenedor | FAS-003, QA-01, DA-004 | 14/14.02 | C4 + secuencia + despliegue | Justificado |
```

Estados permitidos: `Justificado`, `Desviación aprobada` o `No cumple`. Un elemento material sin driver es huérfano y bloqueante.
Usa una fila por elemento material `ARQ/CT/API/TP`; no agrupes varios elementos porque impediría localizar su driver y owner.

### 4. Coherencia por dimensión

Revisa explícitamente:

- alcance/objetivos y exclusiones;
- atributos, tácticas, pruebas y ATAM;
- contenedores, componentes y ownership;
- APIs, eventos, secuencias y contratos;
- datos, fuente de verdad, consistencia, retención y recuperación;
- cobertura `driver → API/OP/evento → schema → DATA → entidad → estructura/store`, nivel de madurez, diccionario por objeto/campo y correspondencia contrato-modelo-físico;
- amenazas, `SEC-xxx`, decisiones y riesgo residual;
- baseline tecnológico, versiones, runtime, hosting e IaC;
- despliegue, resiliencia, observabilidad y operación;
- costos/capacidad contra servicios realmente diseñados;
- roadmap y rollback contra brechas/decisiones.

### 5. Registro de contradicciones y huérfanos

```markdown
### Registro de contradicciones y elementos huérfanos
| ID | Descripción | Artefactos afectados | Severidad | Disposición | Responsable | Estado | Evidencia de cierre |
|---|---|---|---|---|---|---|---|
| CON-001 | Versión distinta de runtime | 10.1, 14.02 | Alta | Corregir baseline | Arquitectura | Cerrada | enlaces |
```

Estados: `Abierta`, `En corrección`, `Cerrada`, `Aceptada`. Una contradicción `Crítica`/`Alta` solo puede cerrar como `Cerrada` o `Aceptada` con `DA-xxx`, riesgo y autoridad.

### 6. ATAM, cobertura y dictamen

Conserva el ATAM por `QA-xx` prioritario definido en la plantilla. Agrega:

```markdown
### Indicadores de cobertura
| Indicador | Numerador | Denominador | Resultado | Umbral | Estado |
|---|---:|---:|---:|---:|---|
| Compromisos aplicables con respuesta | 12 | 12 | 100% | 100% críticos | Cumple |
| Elementos materiales justificados | 18 | 18 | 100% | 100% | Cumple |
| Contradicciones críticas/altas abiertas | 0 | 0 | 0 | 0 | Cumple |
```

Los indicadores apoyan el dictamen; no compensan un bloqueante. Cierra con:

```markdown
### Dictamen de auditoría
**Resultado:** [Apto/Apto con observaciones/No apto]
**Bloqueantes abiertos:** [0/n]
**Fundamento:** [síntesis y enlaces]
```

`Apto con observaciones` solo admite mejoras no bloqueantes con responsable y fecha. El estado de cierre de `25` será `Cumple`, `Cumple con observaciones` o `No cumple` en correspondencia con el dictamen.

## Reglas de cobertura

- 100 % de compromisos críticos aplicables con respuesta y evidencia acorde al escenario.
- 100 % de `QA-xx` prioritarios con respuesta, `TP/DA/CT` y ATAM.
- 100 % de elementos materiales del diseño con driver/decisión.
- 100 % de `DATA-xxx` con owner, fuente de verdad, fila de cobertura y madurez explícita; 100 % de los modelos listos para implementación con esquema físico procesable validado y diccionario exhaustivo; cero tablas, colecciones, vistas, proyecciones o campos físicos sin documentar y cero entradas documentadas inexistentes.
- Cero operaciones ligadas a `FAS/QA` priorizadas en estado `Propuesta` al cerrar `14`-`16`.
- Cero IDs propietarios duplicados o referencias a IDs inexistentes.
- Cero capacidades incluidas perdidas entre `10`, `14` y `17`.
- Cero contradicciones críticas/altas abiertas.
- Cero supuestos críticos vencidos sin disposición.
- Cero artefactos aplicables en `No cumple`.

## Validación automática

Ejecuta desde la raíz del repositorio, después de generar `25`:

```powershell
python .claude/skills/archi/scripts/validate_architecture_coherence.py resources/architecture --scenario A --strict
```

Usa `A`, `B` o `C`. El validador comprueba estructura de `25`, archivos/enlaces, IDs canónicos, owners, cobertura de compromisos y elementos de diseño, estados, placeholders, cierres, contradicciones abiertas y, para DDL SQL, correspondencia entre objetos/campos físicos y `## Diccionario físico de datos`. Registra comando, fecha, salida y versión del script en `25`.

El validador no decide si una táctica es suficiente, si un trade-off es aceptable ni si la arquitectura es adecuada: esas conclusiones requieren revisión experta y ATAM.

## Reauditoría por cambios

Cuando cambie cualquier fuente después de `25`:

1. identifica desde la trazabilidad los artefactos dependientes;
2. vuelve al primer documento dueño afectado y cambia a `No cumple` sus checklists y los dependientes hasta reconciliarlos;
3. si cambia una capacidad, operación o dato, revisa explícitamente contratos ejecutables, catálogo `DATA-xxx`, matriz de persistencia, madurez/modelo físico, secuencias y amenazas antes de repetir el checkpoint correspondiente;
4. actualiza hashes, matrices, ATAM, hallazgos y dictamen de `25`;
5. reejecuta el validador completo, no solo el archivo cambiado;
6. regenera y revalida `25.1`;
7. registra una nueva ronda en `26`.

`00` se genera únicamente desde el snapshot auditado y aprobado.

## Pricing y cobertura de ambientes

Cuando exista `17.4`, exigir el manifiesto `17.4.1` de `contrato-costos.md` y ejecutar `validate_pricing.py` sin mutación. Reconciliar la tabla de inventario de `17` con topología/ambientes, recursos compartidos, categorías facturables y cantidades; el script no descubre omisiones presentes tanto en inventario como en partidas. Confirmar por separado exactitud/vigencia comercial, unidades, descuentos y calibración de consumo. Registrar aproximaciones y pendientes en `04`/`12`/`21` según corresponda. El pricing histórico sin contrato se reporta como brecha; no migrarlo inventando tarifas ni evidencia.
