# Diseño e idiomas Python

Guía de idiomas para cambios en Python. Complementa `python-profile.md`; la
configuración real del proyecto (`pyproject.toml`, linters) prevalece.

## Tipado

- Usa anotaciones de tipo en el código nuevo y en las firmas que modifiques.
- Prefiere tipos del módulo `typing` según la versión objetivo: `list[str]`
  (3.9+), uniones `X | Y` (3.10+), `Self` (3.11+), `type` statement y sintaxis de
  genéricos `def f[T](...)` (3.12+).
- Modelos de datos: `dataclasses` para estructuras simples (con `slots=True` en
  3.10+); `pydantic` cuando haya validación/serialización (FastAPI, contratos).
- No añadas `# type: ignore` sin explicar por qué.

## Estructura y paquetes

- Respeta el layout existente: `src/` (instalable) o plano. No lo cambies.
- Un módulo por responsabilidad; evita `utils.py`-cajón-de-sastre.
- Imports absolutos salvo dentro del propio paquete; orden con `ruff`/`isort`.
- Configura todo en `pyproject.toml` (build, ruff, mypy, pytest, dependencias).

## Dependencias y entorno

- No añadas dependencias sin mandato o justificación; reutiliza las existentes.
- Respeta el gestor del proyecto (`uv`, `poetry`, `pip`/`pip-tools`, `pipenv`) y
  sus lockfiles. No mezcles gestores.
- Runtime vs. dev: las dependencias de test/lint van al grupo `dev`.

## Async

- Usa `asyncio` para I/O-bound; `concurrent.futures` o multiprocessing para
  CPU-bound.
- Prefiere `asyncio.TaskGroup` (3.11+) sobre `asyncio.gather` para cerrar tareas.
- En FastAPI, funciones `async def` solo si hay I/O asíncrono real.

## Errores y recursos

- Excepciones específicas (propias o de stdlib), no `except Exception` a secas.
- Context managers (`with`, `contextlib`) para recursos y limpieza.
- Logging estructurado del proyecto; no `print` para observabilidad.

## API web (si aplica)

- FastAPI: modelos Pydantic de request/response, validación por contrato, OpenAPI
  autogenerado. No inventes endpoints fuera del contrato declarado.
- Flask/Django: sigue las convenciones observadas del proyecto.

## Anti-patrones a evitar

- `except: pass` o `except Exception` sin logging.
- Clases con estado global mutable compartido entre tests.
- `type: ignore`, `noqa` o `pragma: no cover` sin justificación.
