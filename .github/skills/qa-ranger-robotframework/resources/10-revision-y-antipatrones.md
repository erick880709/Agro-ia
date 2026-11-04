# 10 — Revisión y antipatrones

`L` = detectada por `scripts/lint_robot.py`; `M` = revisión manual. Robocop (`-s "DEPR*" -s "ERR*" -s NAME* …`) complementa el estilo.

| # | Antipatrón | Sev. | Det. | Corrección |
|---|---|---|---|---|
| R1 | `Sleep` | Mayor | L | Espera por condición (Wait For…, Wait Until…, `retry_timeout`) |
| R2 | Sintaxis heredada: `[Return]`, `Run Keyword If`, `Exit For Loop`, `Force Tags`, `WITH NAME`, encabezados en singular | Mayor | L | 02 §7, sin superar la versión del runtime |
| R3 | `Set … Variable`, `Create List`, `Catenate` con RF ≥ 7 | Menor | L (`--rf 7`) | `VAR` |
| R4 | Secretos literales (Variables, campos, `Connect To Database`) | **Bloqueante** | L | `%{VAR}` del pipeline / `.env.qa`; rotar si se publicó |
| R5 | URL absoluta en pasos | Mayor | L | `variables/<env>.py` |
| R6 | Test sin verificación (directa o en sus keywords) | **Bloqueante** | L | Aserción del resultado esperado |
| R7 | Test sin ID de caso o prioridad | Mayor | L | `TC-01 [critical] …` + tag del ID |
| R8 | `implicit_wait` > 0 | Mayor | L | `implicit_wait=0s` + esperas explícitas |
| R9 | Clic/escritura con JavaScript | Mayor | L | Esperar interactuabilidad; resolver overlay |
| R10 | `Get WebElement` guardado | Menor | L | Pasar el localizador |
| R11 | SQL con `${variables}` interpoladas | Mayor | L | `parameters=` |
| R12 | SQL destructivo sin filtro / `Delete All Rows From Table` | **Bloqueante** | L | Solo lectura; limpieza acotada por ID |
| R13 | Conexión/navegador sin cierre en el proyecto | Mayor | L | Teardown de suite |
| R14 | Errores tragados (`Run Keyword And Ignore Error` sin usar, `EXCEPT` vacío) | Mayor | L | Dejar fallar o manejar con intención |
| R15 | `FOR`/`IF`/`WHILE`/`TRY` en el cuerpo del test | Menor | L | Keyword de usuario |
| R16 | `Open Browser` sin navegador o nombre inválido | Mayor | L | `${BROWSER}` explícito |
| R17 | `Create Session` sin verificar TLS | Mayor | L | `verify=${True}` o bundle CA |
| R18 | Reintentar acciones no idempotentes (`Wait Until Keyword Succeeds` sobre clic/envío/SQL) | Mayor | L | Reintentar solo verificaciones |
| R19 | Test que publica estado para otros (`scope=SUITE/GLOBAL`) | Mayor | L | Datos propios por test |
| R20 | `robot:skip`/`robot:exclude` sin motivo | Menor | L | `[Documentation]` con ticket |
| R21 | `%{USER}`/`%{HOST}` u otra variable del SO como credencial | Menor | L | `Verificar Variables De Entorno` (08 §4) |
| R22 | DatabaseLibrary registra filas en `log.html` | Menor | L | `log_query_results=False` (2.x) |
| R23 | Clave con `Fill Text`/`Input Text` | Menor | L | `Fill Secret` / `Input Password` |
| R24 | XPath absoluto o posicional | Mayor | L | data-testid, rol, CSS, XPath por texto |
| R25 | Nombres de test duplicados | Mayor | L | Nombres únicos |
| R26 | Browser y SeleniumLibrary en la misma suite | Mayor | L | Una librería web por suite |
| R27 | Rutas absolutas de una máquina | Menor | L | `${CURDIR}`, `${EXECDIR}`, variables |
| R28 | Secreto escrito en el log (`Log    ${PASSWORD}`) | **Bloqueante** | L | No registrar; `Secret` (RF 7.4) |
| R29 | `%{variable}` en minúscula (en Linux Azure DevOps la expone en MAYÚSCULA) | Mayor | L | `%{VARIABLE}` (08 §2) |
| — | Keyword con nombre técnico (clic) en vez de intención | Menor | M | Keywords de negocio |
| — | Aserción que no prueba nada (`Should Be Equal    ${output}    None` tras conectar) | Mayor | M | Verificar el estado de negocio |
| — | Sintaxis más nueva que el runtime del agente | **Bloqueante** | M | Puerta de versión (02 §1) |
| — | Getter de Browser sin operador seguido de `Should …` | Mayor | M | Operador en el getter |

## Revisión manual

- ¿Cada test es independiente y pasa con pabot por test?
- ¿Las esperas esperan la condición de negocio correcta?
- ¿La capa es la adecuada (reglas combinatorias en API/BD, no en UI)?
- ¿Datos sintéticos, usuario de solo lectura y logs sin datos personales?
- ¿La versión de RF/librerías del runtime de CI está registrada y respetada?

## Checklist de PR

- [ ] `lint_robot.py` sin bloqueantes ni mayores; Robocop sin `DEPR`/`ERR`.
- [ ] `robot --dryrun` limpio y al menos una ejecución real de lo modificado.
- [ ] IDs y prioridades en nombres; tags de ID para selección.
- [ ] Línea Base actualizada si cambió versión, ambiente, variables o convenciones.

## Formato del reporte

```markdown
## Revisión Robot Framework — <alcance>
Resumen: X bloqueantes, Y mayores, Z menores. Runtime objetivo: RF <versión>.

### Bloqueantes
1. **[R4] resources/comun.resource:7** — contraseña literal en `Connect To Database`.
   ```robotframework
   Connect To Database    psycopg2    ${DBName}    ${DBUser}    %{PASSWORD}    ${DBHost}    ${DBPort}
   ```
### Mayores / Menores / Cobertura faltante
```
Siempre con el código corregido.
