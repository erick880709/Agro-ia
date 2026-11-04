# 07 — Pruebas de aceptación de base de datos (DatabaseLibrary)

## 1. Qué valida una aceptación de BD

Que el despliegue (scripts DDL/DML, migraciones, procedimientos) dejó la base en el estado que exige la HU o el modelo de datos:

| Tipo | Ejemplo de verificación |
|---|---|
| Esquema | `Table Must Exist`; columnas, tipos y nulabilidad vía `information_schema`/`ALL_TAB_COLUMNS`/`SYSCAT.COLUMNS` |
| Integridad | `Check Row Count    SELECT 1 FROM t WHERE obligatorio IS NULL    ==    0`; huérfanos por FK; duplicados por clave de negocio |
| Datos de referencia / parametrización | catálogos y parámetros cargados con los valores acordados |
| Reglas de negocio en BD | resultado de vistas, funciones, procedimientos (`Call Stored Procedure`) con datos sintéticos |
| Permisos | el usuario de la aplicación puede lo necesario y nada más (`SEC-`) |
| Versión del esquema | tabla de migraciones (Flyway/Liquibase) en la versión del release |

Cada caso tiene un resultado esperado verificable en la fuente; sin él, `[SUPUESTO]` o pregunta.

## 2. Conexión (DatabaseLibrary 2.x)

```robotframework
Library    DatabaseLibrary    log_query_results=False

Conectar A La Base De Datos
    Verificar Variables De Entorno    DB_NAME    DB_HOST    DB_PORT    DB_USER    DB_PASSWORD
    Connect To Database    psycopg2
    ...    db_name=%{DB_NAME}    db_user=%{DB_USER}    db_password=%{DB_PASSWORD}
    ...    db_host=%{DB_HOST}    db_port=%{DB_PORT}
```

- Oracle: `oracledb` (thin por defecto; `oracle_driver_mode=thick,lib_dir=…` con Instant Client; no se puede alternar thin/thick en la misma ejecución). DB2: `ibm_db_dbi`. SQL Server: `pymssql` o `pyodbc` + `odbc_driver={ODBC Driver 18 for SQL Server}`. SQLite: `Connect To Database    sqlite3    database=<ruta>    isolation_level=${None}`.
- Varias bases: `alias=` en la conexión y en cada keyword; cierra con `Disconnect From All Databases`.
- Argumentos posicionales (`Connect To Database    psycopg2    ${db}    ${user}    ${pass}    ${host}    ${port}`) funcionan en 1.x y 2.x: úsalos cuando no conoces la versión del agente (08).
- `config_file=` permite un `.cfg` con parámetros; nunca lo versiones con la clave.

## 3. Verificar

| Keyword (2.x) | Uso |
|---|---|
| `Check Row Count    <select>    ==    0` | cantidades con operador (`==`, `>`, `<=`…) |
| `Check Query Result    <select>    ==    ACTIVA    row=0    col=0` | valor puntual; `assert_as_string=True` si el tipo del driver difiere |
| `Query    <select>    return_dict=True` | filas para aserciones propias |
| `Table Must Exist    cuentas` | existencia |
| `retry_timeout=10s    retry_pause=1s` | esperar un proceso asíncrono (batch, CDC) sin `Sleep` |

Las aserciones son **sensibles al tipo**: `1000` (Decimal) ≠ `"1000"`. Usa `${1000}`, `assert_as_string=True` o convierte.

Deprecadas en 2.x (aún existen, se eliminarán): `Row Count Is 0`, `Row Count Is Equal To X`, `Check If Exists In Database` → `Check Row Count`. Argumentos `selectStatement`/`sansTran` → `select_statement`/`no_transaction`. En agentes con 1.x esas keywords nuevas no existen: `Query` + `Should Be Equal As Integers`.

## 4. Parámetros, nunca concatenación

```robotframework
VAR    @{params}    ${numero}
Check Query Result    SELECT estado FROM cuentas WHERE numero = %s    ==    ACTIVA    parameters=${params}
```

El placeholder depende del driver (`%s` psycopg2/pymssql/pymysql, `:1` oracledb, `?` sqlite3/ibm_db_dbi/pyodbc). Los identificadores (tabla, columna) no se parametrizan: escríbelos literales en la keyword. `replace_robot_variables=True` sustituye `${var}` en el SQL: no lo uses con datos externos.

## 5. Transacciones y efectos

Cada keyword hace commit al terminar y rollback ante error (`no_transaction=True` lo desactiva). Contra ambientes compartidos:
- Usuario de **solo lectura** para aceptación.
- Si un caso debe escribir: inserta datos sintéticos con un identificador del run, verifica y elimina **solo** esos registros en el teardown (`DELETE … WHERE id_prueba = %s`).
- Prohibido en suites de aceptación: `DROP`, `TRUNCATE`, `DELETE`/`UPDATE` sin `WHERE`, `Delete All Rows From Table`.

## 6. Logs y datos sensibles

`log_query_results=True` (por defecto) imprime hasta 50 filas en `log.html`. Con datos de clientes, `log_query_results=False` en el import (2.x) o `Set Logging Query Results    enabled=False`. Selecciona solo las columnas necesarias y nunca `SELECT *` sobre tablas con datos personales.
