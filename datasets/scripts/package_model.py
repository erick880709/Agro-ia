"""Etapa Package (RF-15, sección 19) — empaqueta el modelo versionado.

Genera el manifest del artefacto con versión, hash, configuración y datasets
usados. Salida: datasets/models/<nombre>/<version>/.

Uso:
    python package_model.py --model <dir|archivo> --name coffee-vision \
        --version 1.0.0 --datasets DS01,DS05,DS06
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path

from common import MODELS_DIR, get_logger, load_catalog, sha256_file

log = get_logger("agrovision.package")


def _git_commit() -> str:
    try:
        return subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            capture_output=True,
            text=True,
            check=True,
        ).stdout.strip()
    except Exception:  # noqa: BLE001
        return "unknown"


def empaquetar(modelo: Path, nombre: str, version: str, datasets: list[str]) -> dict:
    destino = MODELS_DIR / nombre / version
    destino.mkdir(parents=True, exist_ok=True)
    if modelo.is_dir():
        for item in modelo.iterdir():
            if item.is_file():
                shutil.copy2(item, destino / item.name)
        artefacto = sorted(destino.glob("*"))[0] if list(destino.glob("*")) else None
    else:
        shutil.copy2(modelo, destino / modelo.name)
        artefacto = destino / modelo.name
    hash_sha = sha256_file(artefacto) if artefacto else None
    catalogo = {d.get("id"): d for d in load_catalog()}
    lineage = [
        {
            "dataset_id": ds_id,
            "version": catalogo.get(ds_id, {}).get("version"),
            "license": catalogo.get(ds_id, {}).get("license"),
            "source_url": catalogo.get(ds_id, {}).get("source_url"),
        }
        for ds_id in datasets
    ]
    manifest = {
        "model_name": nombre,
        "version": version,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "artifact": artefacto.name if artefacto else None,
        "sha256": hash_sha,
        "git_commit": _git_commit(),
        "datasets": lineage,
    }
    (destino / "manifest.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    log.info(
        "package_result",
        extra_fields={"modelo": nombre, "version": version, "sha256": hash_sha},
    )
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser(description="Package — artefacto versionado.")
    parser.add_argument("--model", required=True)
    parser.add_argument("--name", required=True)
    parser.add_argument("--version", required=True)
    parser.add_argument("--datasets", default="", help="IDs separados por coma.")
    args = parser.parse_args()
    datasets = [s.strip().upper() for s in args.datasets.split(",") if s.strip()]
    manifest = empaquetar(Path(args.model), args.name, args.version, datasets)
    print(json.dumps(manifest, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
