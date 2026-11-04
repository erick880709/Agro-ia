# Perfil Python

Capa específica de stack para Builder. No reemplaza el flujo de `SKILL.md`: lo
concreta cuando el componente afectado es Python. Las invariantes del skill
siguen mandando; las convenciones observadas del proyecto y el mandato del
usuario prevalecen sobre cualquier preferencia idiomática de esta guía.

## Activación

Aplica este perfil a cada componente con `pyproject.toml`, `setup.py`,
`requirements.txt`, `Pipfile`, `poetry.lock` o `uv.lock` que el cambio toque. En
monorepos, aplícalo solo a los paquetes Python afectados.

Antes de editar, ejecuta el descubrimiento estático (no instala ni ejecuta nada):

```text
python <skill-root>/scripts/python_toolkit.py discover <ruta-del-paquete>
```

El JSON devuelve, sin ejecutar Python del proyecto: gestor de paquetes y backend
de build, `requires-python`, dependencias, configuración de `ruff`/`mypy`/`pyright`/
`pytest`, layout (`src/` o plano), entornos virtuales y workflows de CI. Si el
script no está disponible, obtén lo mismo leyendo esos archivos. No lo uses como
sustituto de inspeccionar el código afectado.

## Versión objetivo: `requires-python` (o el intérprete) manda

1. `requires-python` de `pyproject.toml` (o `python_requires` de `setup.py`) es
   la versión mínima objetivo del proyecto. El intérprete local puede ser más
   nuevo: eso no habilita features posteriores al mínimo declarado.
2. No uses una feature de lenguaje o de stdlib posterior a la versión objetivo.
   Tabla rápida de gates:

   | Versión | Features habilitadas |
   |---|---|
   | 3.10 | `match/case`, uniones `X | Y`, `dataclasses(slots=True)`, `zoneinfo` |
   | 3.11 | `except*`, `asyncio.TaskGroup`, `tomllib`, mejores mensajes de error |
   | 3.12 | Sintaxis de tipo `def f[T](...)` (PEP 695), `type` statement, mejor f-string |
   | 3.13 | GIL opcional (free-threaded), JIT experimental, `typing.ReadOnly` |

3. No subas `requires-python` ni cambies el gestor de paquetes para usar una
   feature: es una decisión con impacto en CI, imágenes y consumidores. Regístrala
   como decisión pendiente salvo mandato explícito.
4. Dentro de lo permitido por la versión, escribe Python moderno en las líneas que
   crees o modifiques. No migres código vecino que no forma parte del encargo
   (invariante 3 de alcance del diff).
5. Si el proyecto fija estilo con `ruff`, `black`, `isort`, `flake8` o `mypy`, su
   configuración (`pyproject.toml`, `setup.cfg`, `.flake8`) prevalece sobre esta guía.

## Mapa de lectura por tipo de cambio

Lee solo lo que el cambio necesita:

| Necesidad del cambio | Guía |
|---|---|
| Tipado, dataclasses/Pydantic, async, paquetes y dependencias | [Diseño e idiomas](python-design-and-idioms.md) |
| Entrenamiento, evaluación, serving y deuda de ML | [Machine Learning](python-ml.md) |
| Pruebas, lint, type-check y evidencia | [Pruebas y validación Python](python-testing-and-validation.md) |

## Superposición sobre el flujo de Builder

| Paso de Builder | Qué añade el perfil Python |
|---|---|
| 1. Descubrir | `discover`; leer `pyproject.toml`, lockfiles, `.python-version`, CI, `tests/`; ubicar el entrypoint y el cableado real (app, factories, DI) |
| 2. Especificar | Declarar en la spec la versión objetivo, los contratos públicos afectados (firmas, modelos Pydantic, esquemas) y las dependencias nuevas si aplica |
| 3. Diseñar | Elegir la ubicación respetando el layout (`src/` o plano); no introducir un framework nuevo sin mandato |
| 4. Implementar | Regenerar lo generado (clientes, stubs, migraciones, modelos) con el comando del proyecto |
| 5. Validar | Escalera: `ruff` → `mypy`/`ty`/`pyright` → tests focalizados con `pytest` → suite completa → cobertura si está configurada |
| 6. Entregar | Registrar versión de Python, gestor de paquetes, dependencias y comandos validados como contexto de la evidencia |

## Límites del perfil

- No crea proyectos Python nuevos ni layouts globales: eso es baseline o
  arquitectura. Para un repositorio sin paquete de referencia aplica
  [fronteras y fuentes](../../boundaries-and-sources.md).
- No decide la arquitectura de un sistema ML ni reemplaza el flujo de `archi`:
  el perfil ML implementa y valida, no rediseña la topología.
- No instala herramientas (`uv`, `ruff`, `mypy`, `pytest` plugins) sin mandato;
  si faltan, registra la comprobación como `not_run` con razón.

## Fuentes destiladas

Pautas sintetizadas y adaptadas al flujo de Builder a partir de:
`rmyndharis/antigravity-skills` (python-pro), `gvre/skills` (python-developer),
`github/awesome-copilot` (python-pypi-package-builder), `Paldom/python-skills`
(lint/typing/testing/CI), `VoltAgent/awesome-claude-code-subagents` (ml-engineer),
`ml4t/skills` (guardrails de ML) y la documentación oficial de Python (PEPs
484/563/585/604/695), `uv`, `ruff`, `pytest` y `scikit-learn`. Cuando estas
fuentes discrepan (por ejemplo, `mypy` frente a `ty`/`pyright`), la evidencia del
repositorio decide.
