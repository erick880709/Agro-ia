# Migración de datos entre motores y plataformas

Basado en el AI-DLC de migración de bases de datos de AWS (`sample-dbmig-aidlc`:
inception → construction → validation → operations, playbooks Oracle/SQL Server →
PostgreSQL/MySQL) y en las skills de data-migration revisadas.

## Tabla de contenido

1. Fases y gates
2. Evaluación (inception)
3. Conversión (construction)
4. Carga y sincronización
5. Validación de equivalencia
6. Corte y operación
7. Oracle → PostgreSQL: puntos críticos

## 1. Fases y gates

| Fase | Entrega | Gate para avanzar |
|---|---|---|
| Evaluación | Inventario, compatibilidad, esfuerzo, riesgos, estrategia | Plan aprobado (y, si hay archi, reflejado en `23`/`24`) |
| Conversión | DDL destino, código convertido (PL/SQL→PL/pgSQL u otro), cambios de aplicación | Compila y pasa pruebas unitarias en destino |
| Carga/CDC | Full load + replicación continua | Lag dentro del umbral, sin errores |
| Validación | Conteos, checksums, pruebas de equivalencia con datos reales | 0 diferencias no explicadas |
| Corte | Runbook de cutover y rollback | Ensayo exitoso; aprobación del dueño |
| Operación | Monitoreo, tuning, retiro del origen | Estabilidad por el periodo acordado |

## 2. Evaluación

- Inventario: esquemas, tablas, tamaños, tipos, objetos de código (paquetes,
  procedimientos, funciones, triggers, vistas, jobs, sinónimos, db links), dependencias
  externas (ETL, reportes, integraciones), particiones, LOBs.
- Compatibilidad: herramientas (AWS SCT/DMS Schema Conversion, Ora2Pg, SSMA de
  Microsoft) para porcentaje de conversión automática y lista de acciones manuales.
- Estrategia: big bang vs por fases; homogénea vs heterogénea; ventana de corte tolerada
  → full load + CDC cuando la ventana es corta.
- Riesgos: semántica distinta (NULL vs `''` en Oracle, collation/case sensitivity, fechas
  y zonas, precisión numérica, secuencias, transacciones autónomas).

## 3. Conversión

- Tipos: `NUMBER(p,s)`→`NUMERIC(p,s)` (y `NUMBER` sin precisión → decidir `NUMERIC`/
  `BIGINT` por datos reales), `VARCHAR2`→`varchar`/`text`, `DATE` de Oracle (incluye hora)
  →`timestamp(0)`, `CLOB`→`text`, `BLOB`→`bytea`, `RAW(16)`→`uuid` si aplica.
- Código: paquetes → esquemas + funciones; `%TYPE`/`%ROWTYPE` soportados en PL/pgSQL;
  excepciones nombradas; `CONNECT BY`→`WITH RECURSIVE`; `ROWNUM`→`LIMIT`/`ROW_NUMBER()`;
  `DECODE`→`CASE`; `NVL`→`COALESCE`; `SYSDATE`→`now()`/`clock_timestamp()` según semántica;
  transacciones autónomas → `dblink`/rediseño; `DBMS_*` → extensiones (`orafce`, `pg_cron`)
  o la aplicación.
- Mantén la lógica en la base solo si sigue justificándose (ver procedimientos).

## 4. Carga y sincronización

- Full load con herramientas del destino (AWS DMS, `COPY`, Data Pump/`expdp` en
  homogéneas, `bcp`/BULK INSERT) desactivando temporalmente índices secundarios y FK en
  destino, y recreándolos/validándolos después.
- CDC: AWS DMS, Oracle GoldenGate, Debezium (Kafka) u otro aprobado; supervisa lag,
  LOBs, tablas sin PK (CDC las maneja mal) y DDL durante la replicación.
- Secuencias/identities ajustadas al máximo del origen antes del corte.

## 5. Validación de equivalencia

1. Conteos por tabla y por partición/ventana.
2. Checksums/hash por lotes de columnas normalizadas (cuidado con formato de fechas,
   espacios, precisión).
3. Muestras de registros comparadas campo a campo.
4. Pruebas de equivalencia de **código**: mismas entradas reales → mismas salidas
   (funciones, procedimientos, vistas), dentro de transacción con rollback.
5. Pruebas de la aplicación (regresión funcional y de rendimiento con planes del destino).

## 6. Corte y operación

Runbook con tiempos: congelar escrituras o modo solo lectura, drenar CDC a lag 0,
validación final, ajustar secuencias, cambiar conexiones (DNS/secretos), smoke tests,
criterios de rollback y por cuánto tiempo se mantiene el origen sincronizado en reversa.
Tras el corte: estadísticas (`ANALYZE`), monitoreo de planes y retiro planificado del
origen con respaldo final.

## 7. Oracle → PostgreSQL: puntos críticos

`''` vs `NULL`; comparación de strings case-sensitive en PG; `DATE` con hora;
`NUMBER` sin precisión; secuencias con `CACHE`; paquetes con estado de sesión; jobs
(`DBMS_SCHEDULER`) → `pg_cron` o planificador externo; sinónimos y db links; hints
(no existen en PG sin `pg_hint_plan`); particionamiento y tablespaces; jerarquías
`CONNECT BY`; funciones analíticas compatibles; outer joins `(+)`.
