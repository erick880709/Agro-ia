# Guía: diccionario físico de datos

Aplica cuando un `16.xx` alcanza nivel físico o enlaza un asset procesable `16.xx.y`. El DDL, ORM o esquema ejecutable define la estructura; el diccionario explica su semántica, gobierno y uso. Ninguno sustituye al otro.

## Contenido

1. [Cobertura obligatoria](#1-cobertura-obligatoria)
2. [Formato por tabla o colección](#2-formato-por-tabla-o-colección)
3. [Formato por vista o proyección](#3-formato-por-vista-o-proyección)
4. [Correspondencia con el esquema](#4-correspondencia-con-el-esquema)
5. [Gate de cierre](#5-gate-de-cierre)

## 1. Cobertura obligatoria

Documenta en el `16.xx` dueño el 100 % de los objetos físicos declarados por cada `16.xx.y`: tablas, colecciones, vistas, proyecciones materializadas, índices de búsqueda u objetos equivalentes. Incluye también catálogos, tablas puente, historiales, tablas de auditoría y objetos técnicos que soporten una capacidad; no documentes únicamente los agregados principales.

Cada objeto físico debe:

- usar su nombre completamente calificado cuando el motor tenga schema o namespace;
- enlazar al menos un `DATA-xxx` canónico;
- declarar propósito, owner, clasificación, retención/borrado, seguridad y consumidores/operaciones;
- explicar si es fuente de verdad, réplica, historial, proyección, caché o auditoría;
- documentar todos sus campos/columnas observables;
- corresponder exactamente con el asset procesable, sin objetos ni campos huérfanos.

No declares el nivel físico `Completo` si existe un objeto o campo sin documentación, o una entrada documentada que no existe en el esquema.

## 2. Formato por tabla o colección

El `16.xx` contiene una sección con el encabezado exacto `## Diccionario físico de datos` y una subsección por objeto:

```markdown
### `app.employee` — Tabla

- **DATA:** DATA-001
- **Propósito:** Fuente de verdad del empleado dentro del bounded context.
- **Owner:** CT-03 / Equipo Nómina
- **Rol del dato:** Agregado transaccional / fuente de verdad
- **Clasificación:** PII
- **Retención/borrado:** Política LEG-001; anonimización al vencer el plazo
- **Seguridad/RLS:** Aislamiento por tenant y mínimo privilegio
- **Índices/particiones:** PK por employee_id; índice tenant_id; sin partición inicial
- **Consumidores/operaciones:** API-002-OP-001, job payroll-close

| Columna | Tipo | Nulo | Default | Clave/referencia | Restricciones | Clasificación/PII | Descripción |
|---|---|---|---|---|---|---|---|
| employee_id | uuid | No | gen_random_uuid() | PK | — | Interno | Identificador estable |
| tenant_id | uuid | No | — | FK tenant.tenant_id | — | Interno | Tenant propietario |
```

Usa `N/A — <motivo>` cuando una celda no aplique; no la dejes vacía. Para tablas puente o técnicas conserva el mismo formato. En motores no relacionales reemplaza `Columna` por `Campo/ruta`, y documenta estructura anidada, cardinalidad y reglas de evolución.

## 3. Formato por vista o proyección

Usa el mismo patrón con tipo `Vista`, `Vista materializada`, `Proyección` u otro equivalente:

```markdown
### `reporting.v_employee_summary` — Vista

- **DATA:** DATA-013
- **Propósito:** Proyección de lectura para BI.
- **Owner:** CT-03 / Equipo Nómina
- **Rol del dato:** Proyección derivada, no fuente de verdad
- **Clasificación:** PII minimizada
- **Retención/borrado:** Heredada de las fuentes
- **Seguridad/RLS:** Rol de solo lectura y filtros por tenant
- **Índices/particiones:** N/A — vista no materializada
- **Consumidores/operaciones:** Power BI
- **Fuentes/frescura:** app.employee; lectura en tiempo real

| Columna | Tipo | Nulo | Default | Clave/referencia | Restricciones | Clasificación/PII | Descripción |
|---|---|---|---|---|---|---|---|
| employee_id | uuid | No | N/A — derivada | Referencia lógica | — | Interno | Identificador del empleado |
```

Enumera la salida pública de la vista incluso si el DDL usa `SELECT *`; preferiblemente evita `SELECT *` para impedir cambios de contrato accidentales.

## 4. Correspondencia con el esquema

Para SQL, `validate_architecture_coherence.py` compara automáticamente:

- cada `CREATE TABLE` y `CREATE VIEW` con una subsección del diccionario;
- cada columna física de tabla con una fila del diccionario;
- entradas documentadas inexistentes en el asset;
- presencia de los campos semánticos y de gobierno obligatorios;
- encabezados mínimos del diccionario de columnas.

La comparación automática no demuestra que la descripción sea correcta ni que una clasificación sea legalmente suficiente. La revisión experta debe comprobar semántica, invariantes, ownership, privacidad, retención, índices, RLS, migración y correspondencia con contratos.

Para formatos que el validador no pueda inspeccionar, genera un inventario procesable con la herramienta nativa y registra comando/resultado. La ausencia de soporte automático no reduce la obligación de cobertura.

## 5. Gate de cierre

Antes de declarar el nivel físico `Completo`:

- documenta el 100 % de objetos y campos del esquema;
- asigna cada objeto a `DATA-xxx`, owner y rol del dato;
- registra PK/FK o equivalentes, nulabilidad, defaults, restricciones e índices relevantes;
- documenta clasificación por campo, retención, borrado, cifrado, RLS/ACL y auditoría aplicables;
- documenta vistas/proyecciones, fuentes, consumidores y frescura;
- valida que esquema y diccionario no tengan diferencias;
- actualiza simultáneamente DDL, diccionario, snapshot de `25` y presentación derivada cuando cualquiera cambie.

Una diferencia entre el esquema y el diccionario es bloqueante para `CP-03` y `AUD-25` cuando el objetivo sea `Listo para implementación`.
