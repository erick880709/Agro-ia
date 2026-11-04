# 02 — Lenguaje y sintaxis

## 1. Puerta de versión

Establece la versión del runtime **donde corre la suite** antes de escribir:

| Característica | RF mínimo |
|---|---|
| `RETURN`, `BREAK`, `CONTINUE`, `TRY/EXCEPT` | 5.0 |
| `Test Tags`, `Keyword Tags`, `robot:private`, `AS` en imports | 6.0 |
| `VAR`, `[Tags]    -tag` | 7.0 |
| `VAR … scope=SUITES` | 7.1 |
| `GROUP`, `(?i)` en embebidos | 7.2 |
| Argumentos tipados `${n: int}`, `VAR` tipado | 7.3 |
| Tipo `Secret` | 7.4 |

- `${n: int}` en RF < 7.3 **pasa el dry run** y falla al ejecutar. `${n}: int` es inválido siempre.
- Release corporativo con versión desconocida ⇒ escribe RF 5 (sin `VAR`, sin `Test Tags` si puede ser RF 5; usa `[Tags]` por test).

## 2. Esqueleto

```robotframework
*** Settings ***
Documentation     Qué cubre la suite y su fuente (HU, modelo de datos).
Resource          ../resources/cuentas.resource
Suite Setup       Conectar A La Base De Datos
Suite Teardown    Desconectar De La Base De Datos
Test Tags         database

*** Test Cases ***
TC-01 [critical] [HU-120][CA-1] Una cuenta activa conserva su saldo
    [Tags]    TC-01    smoke
    La Cuenta "0001" Tiene Estado "ACTIVA"

*** Keywords ***
La Cuenta "${numero}" Tiene Estado "${estado}"
    VAR    @{params}    ${numero}
    Check Query Result    SELECT estado FROM cuentas WHERE numero = %s    ==    ${estado}    parameters=${params}
```

Cada archivo empieza con un encabezado de sección en **plural**. Separador: 4 espacios (mínimo 2). Setting de keyword en orden: `[Documentation]`, `[Tags]`, `[Arguments]`, `[Timeout]`, `[Setup]`, cuerpo, `[Teardown]`.

## 3. Variables y alcance

- `VAR    ${x}    valor    scope=TEST|SUITE|SUITES|GLOBAL` (RF 7); antes, `Set Test/Suite/Global Variable`.
- Mayúsculas para variables no locales; minúsculas para locales y argumentos.
- Prioridad: `--variable` > `--variablefile` > `*** Variables ***` propias > resources importados.
- `%{NOMBRE}` lee el entorno y falla si no existe; `%{NOMBRE=defecto}` define un valor por defecto (no lo uses para secretos).
- Expresiones: `IF    $saldo > 0` usa la variable como objeto Python; `${saldo} > 0` sustituye texto.

## 4. Control de flujo (dentro de keywords, no en el test)

```robotframework
Registrar Si Hay Diferencias
    [Arguments]    @{filas}
    FOR    ${fila}    IN    @{filas}
        IF    $fila[1] is None    CONTINUE
        Should Not Be Empty    ${fila}[1]
    END
    TRY
        Table Must Exist    auditoria
    EXCEPT    *does not exist*    type=glob
        Fail    Falta la tabla de auditoría en el despliegue
    END
```

## 5. Argumentos

| Necesidad | Forma |
|---|---|
| Obligatorio / opcional | `${a}` / `${b}=defecto` |
| Variable | `@{items}`; solo nombrados después: `@{}    ${timeout}=10s` |
| Libres nombrados | `&{opciones}` (al final) |
| Valor dentro del nombre (BDD) | `La Cuenta "${numero}" Existe` — comillas evitan capturas ambiguas |
| Conversión | `${n: int}` (7.3+) o `Convert To Integer` |

Argumentos nombrados se escriben literal y sin espacio antes de `=`: `timeout=5s`. `timeout =5s` se pasa como posicional y el dry run no lo detecta.

## 6. Data-driven y BDD

```robotframework
*** Settings ***
Test Template     Rechazar Monto Invalido

*** Test Cases ***                          MONTO      MOTIVO
TC-11 [high] Monto cero se rechaza          0          monto_invalido
TC-12 [high] Monto negativo se rechaza      -1         monto_invalido
```

BDD: `Given/When/Then/And/But` se omiten al resolver; define los pasos **sin** prefijo (`La Cuenta "0001" Existe`). Un template ejecuta todas las filas aunque una falle.

## 7. Migración heredado → moderno

| Heredado | Moderno | RF mín. | Robocop |
|---|---|---|---|
| `[Return]    ${x}` | `RETURN    ${x}` | 5.0 | DEPR11 |
| `Run Keyword If` / `Unless` | `IF` / `ELSE` | 4.0 | DEPR08 |
| `Exit For Loop`, `Continue For Loop` | `BREAK`, `CONTINUE` | 5.0 | DEPR09 |
| `Set Test/Suite/Global Variable` | `VAR … scope=` | 7.0 | DEPR05 |
| `Create List`, `Create Dictionary` | `VAR    @{l}` / `VAR    &{d}` | 7.0 | DEPR06 |
| `Force Tags` / `Default Tags` | `Test Tags` + `[Tags]    -tag` | 6.0 | DEPR07 |
| `WITH NAME` | `AS` | 6.0 | DEPR03 |
| `*** Setting ***`, `*** Test Case ***` | Plural | 6.0 | DEPR04 |
| `Run Keyword And Ignore Error` como control | `TRY/EXCEPT` | 5.0 | — |

Reescribe un archivo a la vez, sin superar la versión del runtime; luego dry run, Robocop (`-s "DEPR*"`) y ejecución real.
