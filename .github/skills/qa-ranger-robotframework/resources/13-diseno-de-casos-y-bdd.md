# 13 — Diseño de casos y BDD

## 1. De la fuente a los casos

1. Lista los requisitos con su ID real (HU, CA, RF, regla del modelo de datos). No inventes IDs.
2. Por requisito aplica: partición de equivalencias, valores límite, tabla de decisión para reglas combinadas, transición de estados para entidades con estados (cuenta: ACTIVA → BLOQUEADA → CERRADA), y negativos.
3. Elige la capa más barata que lo prueba: integridad y parametrización en BD; reglas y contratos en API; solo flujos críticos en web.
4. Deduplica: un caso por comportamiento observable; las variantes de datos van como filas de template.
5. Cada caso: `id`, `requisitos`, precondición/datos, pasos, **resultado esperado verificable**, prioridad. Exclusiones con motivo.

## 2. Casos típicos de aceptación de BD

| Requisito | Caso |
|---|---|
| "Se crea la tabla de movimientos con FK a cuentas" | tabla existe; FK presente; 0 movimientos huérfanos |
| "El campo estado es obligatorio y toma ACTIVA/BLOQUEADA/CERRADA" | 0 nulos; 0 valores fuera del dominio |
| "Se carga el parámetro TOPE_DIARIO = 5.000.000" | `Check Query Result … == ${5000000}` |
| "El procedimiento recalcula saldos" | ejecutar con datos sintéticos propios y verificar el resultado; limpiar |
| "El usuario de la app no puede borrar auditoría" | intento de `DELETE` con ese usuario falla (`SEC-`) — solo en ambiente autorizado |

## 3. Data-driven

`Test Template` con encabezados de columna; una fila = un caso con su propio ID (`TC-11 [high] …`). Para conjuntos grandes o mantenidos por negocio, DataDriver (`robotframework-datadriver`) con CSV/Excel versionado sin datos reales.

## 4. BDD / Gherkin en Robot

```robotframework
*** Test Cases ***
TC-21 [critical] [HU-140][CA-1] Bloquear una cuenta activa
    [Tags]    TC-21
    Given La Cuenta "9001" Está En Estado "ACTIVA"
    When Se Ejecuta El Bloqueo De La Cuenta "9001"
    Then La Cuenta "9001" Queda En Estado "BLOQUEADA"
```

Los pasos se definen sin prefijo y con argumentos embebidos entre comillas. Si el equipo ya usa archivos `.feature`, Robot no los ejecuta de forma nativa: evalúa mantener Cucumber/Karate o la guía BDD de Ranger (`../ranger/references/tools/bdd_gherkin_patterns.md`).

## 5. Plantilla de caso

| ID | Requisitos | Prioridad | Datos | Pasos | Resultado esperado |
|---|---|---|---|---|---|
| TC-01 | HU-120/CA-1 | critical | cuenta sintética 9001 | consultar estado | `ACTIVA` |
