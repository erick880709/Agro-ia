# 14 — Librerías Python, listeners y migración

## 1. Cuándo escribir una librería Python

Cuando la lógica necesita Python (parsear, firmar, comparar estructuras, protocolos). Componer keywords existentes sigue siendo una keyword de usuario.

```python
from robot.api.deco import keyword, library

@library(scope="SUITE", auto_keywords=False)
class Saldos:
    @keyword("Diferencia De Saldos Debe Ser Cero")
    def diferencia(self, esperado: float, actual: float):
        if round(esperado - actual, 2) != 0:
            raise AssertionError(f"Diferencia {esperado - actual:.2f}")
```

- `scope` según la vida del estado: `TEST` (por defecto), `SUITE` o `GLOBAL`.
- Tipos en la firma ⇒ conversión automática. Falla con `AssertionError` y mensaje de negocio.
- Sin `print` de secretos; `robot.api.logger` para registrar.
- Verifica con `python -m robot.libdoc libraries/Saldos.py list`.

## 2. Listeners (API v3)

Para enganchar evidencia, métricas o integración con herramientas (`--listener libraries/MiListener.py`). Un listener no debe cambiar el resultado de los tests sin dejar rastro.

## 3. Migración de sintaxis

Sigue 02 §7: un archivo a la vez, sin superar la versión del runtime; Robocop `--target-version`; dry run; ejecución real.

## 4. Migración entre librerías y herramientas

| De → a | Nota |
|---|---|
| SeleniumLibrary → Browser | Por suite; cambian esperas (Browser espera solo), selectores (`id=` vs `id:`) y evidencia (video/trace nativos). Mantén los IDs `TC-xxx`. |
| DatabaseLibrary 1.x → 2.x | Renombrar argumentos (`selectStatement`→`select_statement`, `dbapiModuleName`→`db_module`); `Row Count Is 0` → `Check Row Count … == 0`. |
| Selenium Java/pytest → Robot | Solo si el equipo lo decide; conserva IDs y corre ambas suites en paralelo durante la transición (`../ranger/references/tools/tool_migration_guide.md`). |
| Robot → Playwright/Karate | Fuera de esta skill: aplicar `qa-ranger-playwright` o `qa-ranger-karate`. |

No migres en silencio porque el usuario mencionó otra herramienta: confirma alcance.

## 5. Móvil

AppiumLibrary (`robotframework-appiumlibrary`) sigue las reglas de esta skill para estructura, nombres y evidencia; las capacidades, gestos e infraestructura están en `../ranger/references/tools/appium_mobile_patterns.md`. Confirma dispositivo/emulador antes de generar casos.
