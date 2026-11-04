#!/usr/bin/env python3
"""python_toolkit.py — Descubrimiento estático de proyectos Python para Builder.

Solo lee archivos; no instala dependencias ni ejecuta el código del proyecto.
Uso: python python_toolkit.py discover <ruta-del-paquete>
"""
import json
import os
import sys
from pathlib import Path

MANIFESTS = ["pyproject.toml", "setup.py", "setup.cfg", "requirements.txt", "Pipfile", "poetry.lock", "uv.lock"]


def _read_toml(path: Path):
    try:
        import tomllib  # Python 3.11+
        return tomllib.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def _package_manager(root: Path):
    if (root / "uv.lock").exists():
        return "uv"
    if (root / "poetry.lock").exists() or (root / "pyproject.toml").exists() and _uses_poetry(root):
        return "poetry"
    if (root / "Pipfile").exists():
        return "pipenv"
    if (root / "requirements.txt").exists():
        return "pip"
    return None


def _uses_poetry(root: Path):
    try:
        import tomllib
        data = tomllib.loads((root / "pyproject.toml").read_text(encoding="utf-8"))
        return "poetry" in (data.get("tool") or {})
    except Exception:
        return False


def discover(path: str) -> dict:
    root = Path(path).resolve()
    result = {
        "root": str(root),
        "is_python": any((root / m).exists() for m in MANIFESTS),
        "manifests": [m for m in MANIFESTS if (root / m).exists()],
        "package_manager": _package_manager(root),
        "requires_python": None,
        "build_backend": None,
        "dependencies": [],
        "dev_dependencies": [],
        "ruff": False,
        "mypy": False,
        "pyright": False,
        "pytest": False,
        "layout": "flat",
        "test_dirs": [],
        "ci_workflows": [],
    }

    if (root / "pyproject.toml").exists():
        data = _read_toml(root / "pyproject.toml")
        if data:
            project = data.get("project") or {}
            result["requires_python"] = project.get("requires-python")
            result["dependencies"] = project.get("dependencies") or []
            result["dev_dependencies"] = ((project.get("optional-dependencies") or {}).get("dev")) or []
            bs = data.get("build-system") or {}
            result["build_backend"] = bs.get("build-backend")
            tool = data.get("tool") or {}
            result["ruff"] = "ruff" in tool
            result["mypy"] = "mypy" in tool
            result["pyright"] = "pyright" in tool
            result["pytest"] = "pytest" in tool

    if (root / "src").is_dir():
        result["layout"] = "src"

    for d in ("tests", "test"):
        if (root / d).is_dir():
            result["test_dirs"].append(d)

    ci = root / ".github" / "workflows"
    if ci.is_dir():
        result["ci_workflows"] = [p.name for p in ci.glob("*.yml")] + [p.name for p in ci.glob("*.yaml")]

    return result


def main(argv):
    if len(argv) < 3 or argv[1] != "discover":
        print(__doc__, file=sys.stderr)
        return 2
    print(json.dumps(discover(argv[2]), indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
