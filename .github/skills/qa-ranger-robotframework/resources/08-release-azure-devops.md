# 08 — Stage "Acceptance Test" en releases de Azure DevOps (agentes Linux)

Estándar para pruebas de aceptación de bases de datos con Robot Framework en el pool de agentes de automatización. Perfil de scaffold: `db-release` (genera `acceptance_test/` y `PIPELINE_RELEASE.md`).

## 1. Estructura esperada

```
<repositorio>/
└── acceptance_test/
    ├── resources/connection_database.resource
    ├── libraries/QaEvidencia.py
    └── test_cases/*.robot          # "Test Cases Path" de la tarea
```

El artefacto del build publica `acceptance_test`; en el release la ruta es `$(System.DefaultWorkingDirectory)/_<ARTEFACTO>/acceptance_test/test_cases`.

## 2. Variables en MAYÚSCULA

Azure DevOps expone las variables del pipeline como variables de entorno con el nombre en mayúscula (y `.` → `_`). En Linux `%{db}` y `%{DB}` son distintas: escribe la forma en mayúscula.

```robotframework
*** Variables ***
${DBName}    %{DB}
${DBHost}    %{HOST}
${DBPort}    %{PORT}
${DBUser}    %{USER}
${DBPass}    %{PASSWORD}
```

| Variable del pipeline | En Robot |
|---|---|
| `DB`, `HOST`, `PORT`, `USER`, `PASSWORD` | `%{DB}` … `%{PASSWORD}` |
| `keyPath` | `%{KEYPATH}` |
| `ma_db_user` | `%{MA_DB_USER}` |

Las variables **secretas** no llegan al proceso por defecto: en YAML hay que mapearlas en `env:`; en el release clásico, la tarea `RobotFramework-DBLibrary` versión `2.*` es la que permite manejarlas ocultas.

## 3. Tareas del Agent job

1. **RobotFramework-DBLibrary** `2.*` — Test Cases Path: `…/acceptance_test/test_cases`.
2. **AutomationUse** — Testing Framework: *Robot Framework*; Path of main folder: `…/acceptance_test/test_cases`; Test Result folder path: `…/acceptance_test`; Repository name; AWS Credentials del equipo.
3. **Publish Report** (Publish HTML Report).

Confirma nombres y versiones de tareas en tu organización: son extensiones internas. Deja el resto de opciones por defecto salvo indicación del equipo de DevOps.

## 4. Gotcha crítico: `%{USER}` y `%{HOST}`

`USER` (y en algunos shells `HOST`) ya existen en el sistema del agente. Si el secreto no se inyecta, `%{USER}` **no falla**: devuelve el usuario del agente y el error aparece como `password authentication failed for user "<agente>"`, que parece un problema de credenciales. La plantilla llama primero a:

```robotframework
Verificar Variables De Entorno    DB    HOST    PORT    USER    PASSWORD
```

que falla si alguna falta, está vacía o conserva el valor del sistema (compara con el usuario real del proceso, no con `$USER`). Comprobado con PostgreSQL 16: con `USER` sin inyectar la suite se detiene con «USER: tiene el valor del agente (root); el pipeline no la inyectó».

## 5. Versión del runtime del agente

La tarea trae su propio Robot Framework, DatabaseLibrary y drivers. Hasta verificarlos en el log:
- Sintaxis RF 5 (sin `VAR`); `Create List` para parámetros.
- `Connect To Database` posicional (módulo, base, usuario, clave, host, puerto): válido en DatabaseLibrary 1.x y 2.x.
- `Query` + `Should Be Equal As Integers/Strings` en vez de `Check Row Count`/`Check Query Result` (no existen en 1.4.4; sí en 2.x). `parameters=` existe desde 1.3.
- `log_query_results=False` existe solo en 2.x: confirma la versión antes de añadirlo al import.

Ejemplo heredado frecuente y su corrección:

```robotframework
# Heredado: no copiar
Connect to database postgresql
    ${output}    Connect To Database    psycopg2    ${DBName}    ${DBUser}    ${DBPass}    ${DBHost}    ${DBPort}
    should be equal as strings    ${output}    None
    [Return]    ${output}
```

`Connect To Database` devuelve `None`; esa aserción no verifica nada y `[Return]` es obsoleto. Conecta en `Suite Setup`, desconecta en `Suite Teardown` y verifica en los tests.

## 6. Errores frecuentes

| Log | Causa | Acción |
|---|---|---|
| `Variable '%{DB}' not found` | minúsculas o scope de la variable | MAYÚSCULA y scope Release/stage |
| `password authentication failed for user "<agente>"` | `%{USER}` del sistema | guarda de entorno; revisar inyección de secretos |
| `No module named 'psycopg2'` / `'oracledb'` | driver ausente en el runtime | solicitar el driver al equipo de la tarea |
| `No keyword with name 'Check Row Count'` | DatabaseLibrary 1.x | `Query` + aserción BuiltIn |
| `Suite setup failed … could not connect … timeout` | red del agente al motor | regla de firewall/ruta; no reintentar en bucle |
| `contains no tests` | ruta apunta a la carpeta equivocada o archivo sin `*** Test Cases ***` | revisar Test Cases Path |

## 7. Equivalente en pipeline YAML

Si el equipo usa YAML con tareas estándar: `UsePythonVersion@0`, `pip install -r requirements.txt`, `./ejecutar.sh` con `env:` que mapee `DB: $(DB)`, `USER: $(USER)`, …, `PublishTestResults@2` (JUnit desde `--xunit`) y `PublishPipelineArtifact@1` de `resources/qa`. Plantilla: `templates/common/azure-pipelines.yml`.
