# Pruebas y validación Python

Escalera de validación para cambios en Python. Ejecuta en orden; detente en el
primer fallo real y corrígelo antes de continuar.

## Escalera

1. **Formato/lint** — `ruff check` y `ruff format --check` (o el linter del
   proyecto: black/isort/flake8). Sin errores de estilo en el diff.
2. **Type check** — `mypy` (o `ty`/`pyright` según el proyecto). Errores nuevos en
   el código tocado son bloqueantes.
3. **Tests focalizados** — `pytest <ruta-del-módulo-o-test>` para lo afectado.
4. **Suite completa** — `pytest` en el paquete/componente.
5. **Cobertura** — `pytest --cov` solo si el proyecto la configura; no impongas un
   umbral que el repo no tenga.

Cada comprobación que no pueda ejecutarse (herramienta ausente, entorno no
disponible) se registra como `not_run` con razón; no se cuenta como aprobada.

## Tests

- `pytest` es el runner por defecto. Usa `fixtures`, `parametrize` y `tmp_path`.
- Casos positivos y negativos; en ML, un test que fije la métrica de referencia
  con un dataset pequeño y determinista.
- No modifiques código bajo prueba para alcanzar cobertura.
- Si el proyecto usa `tox`/`nox`/`uv`, ejecuta el comando que el repo declara.

## Comandos (respetando el gestor del proyecto)

```text
uv run pytest ...            # proyecto uv
poetry run pytest ...        # proyecto poetry
python -m pytest ...         # pip/venv
```

## Evidencia

Registra: comando ejecutado, resultado (pass/fail/not_run), versión de Python,
gestor de paquetes y alcance (tests focalizados vs suite completa).
