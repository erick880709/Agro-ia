"""Etapa Inspect (11.3) — integridad, MIME, resolución y labels.

Recorre raw/<DS>/<version>/ y valida cada imagen decodificable (RF-05),
dimensiones, formato y profundidad de bits. Elementos corruptos, de licencia
dudosa o de estructura inesperada se mueven a quarantine/ sin borrarse.

NOTA: este archivo se llama `inspect.py` por especificación y puede
enmascarar el módulo `inspect` de la stdlib cuando datasets/scripts está en
sys.path. Por eso retira su propio directorio de sys.path ANTES de cualquier
otro import (common.py hace lo mismo); los demás scripts importan `common`
antes que numpy para heredar ese saneo. Los imports del pipeline se hacen
dentro de las funciones para evitar importaciones circulares.

Uso:
    python inspect.py [--ids DS01,DS02]
"""

from __future__ import annotations

import importlib.util as _importlib_util
import sys
import sysconfig as _sysconfig
from pathlib import Path

_SCRIPT_DIR = Path(__file__).resolve().parent


def _es_script_dir(entrada: str) -> bool:
    if not entrada:
        entrada = "."
    try:
        return Path(entrada).resolve() == _SCRIPT_DIR
    except OSError:
        return False


sys.path[:] = [p for p in sys.path if not _es_script_dir(p)]
# Reinsertar al final: la stdlib conserva prioridad sobre `inspect.py`.
sys.path.append(str(_SCRIPT_DIR))

# Proxy transparente del módulo stdlib `inspect`. Se carga por archivo
# explícito (spec_from_file_location NO consulta sys.modules, donde el nombre
# `inspect` apunta a este módulo parcial durante su importación).
_inspect_path = Path(_sysconfig.get_paths()["stdlib"]) / "inspect.py"
_spec = _importlib_util.spec_from_file_location("agrovision_stdlib_inspect", _inspect_path)
_stdlib_inspect = _importlib_util.module_from_spec(_spec)
_spec.loader.exec_module(_stdlib_inspect)
globals().update(
    {k: v for k, v in vars(_stdlib_inspect).items() if not k.startswith("__")}
)

import argparse  # noqa: E402
import mimetypes  # noqa: E402
import shutil  # noqa: E402
from datetime import datetime, timezone  # noqa: E402

_SIGNATURES = {
    b"\xff\xd8\xff": "image/jpeg",
    b"\x89PNG\r\n\x1a\n": "image/png",
    b"RIFF": "image/webp",
    b"II*\x00": "image/tiff",
    b"MM\x00*": "image/tiff",
}


def sniff_mime(data: bytes) -> str:
    for signature, mime in _SIGNATURES.items():
        if data.startswith(signature):
            return mime
    return mimetypes.guess_type("x.bin")[0] or "application/octet-stream"


def _decode_image(path: Path) -> dict | None:
    """Intenta decodificar con Pillow (presente en el entorno de datos)."""
    try:
        from PIL import Image  # type: ignore
    except ImportError:
        return {"error": "pillow_no_disponible"}
    try:
        with Image.open(path) as img:
            img.verify()
        with Image.open(path) as img:
            info = {
                "format": img.format,
                "mode": img.mode,
                "width": img.width,
                "height": img.height,
            }
            if "tiff" in (info["format"] or "").lower():
                info["frames"] = getattr(img, "n_frames", 1)
            return info
    except Exception as exc:  # noqa: BLE001
        return {"error": f"no_decodificable: {exc}"}


def inspeccionar_dataset(ds: dict, config: dict) -> list[dict]:
    from common import (  # noqa: E402  (import diferido, ver docstring)
        IMAGE_EXTENSIONS,
        QUARANTINE_DIR,
        RAW_DIR,
        sha256_file,
    )

    version = ds.get("version") or "current"
    raiz = RAW_DIR / ds.get("id") / version
    if not raiz.exists():
        return []
    min_size = config.get("inspect", {}).get("min_size_px", 32)
    allowed = set(
        config.get("inspect", {}).get("allowed_extensions")
    ) or IMAGE_EXTENSIONS
    records: list[dict] = []
    for path in sorted(raiz.rglob("*")):
        if not path.is_file() or path.suffix == ".part":
            continue
        record = {
            "dataset_id": ds.get("id"),
            "version": version,
            "archivo": str(path.relative_to(raiz)),
            "size": path.stat().st_size,
            "inspeccionado_en": datetime.now(timezone.utc).isoformat(),
        }
        if path.suffix.lower() not in allowed:
            record.update(estado="quarantine", motivo="extension_no_permitida")
        else:
            data = path.read_bytes()[:16]
            record["mime"] = sniff_mime(data)
            decoded = _decode_image(path)
            if isinstance(decoded, dict) and "error" in decoded:
                record.update(estado="quarantine", motivo=decoded["error"])
            else:
                record.update(decoded or {})
                if decoded and min(decoded.get("width", 0), decoded.get("height", 0)) < min_size:
                    record.update(estado="quarantine", motivo="imagen_demasiado_pequena")
                else:
                    record["sha256"] = sha256_file(path)
                    record["estado"] = "ok"
        if record.get("estado") == "quarantine":
            destino = QUARANTINE_DIR / ds.get("id") / version / record["archivo"]
            destino.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(path), str(destino))
        records.append(record)
    return records


def main() -> None:
    from common import (
        METADATA_DIR,
        append_jsonl,
        get_logger,
        load_catalog,
        load_pipeline_config,
    )

    parser = argparse.ArgumentParser(description="Inspect — valida integridad de imágenes.")
    parser.add_argument("--ids", default="", help="IDs separados por coma (vacíos = todos).")
    args = parser.parse_args()

    ids = {s.strip().upper() for s in args.ids.split(",") if s.strip()}
    config = load_pipeline_config()
    salida = METADATA_DIR / "inspection.jsonl"
    total: dict[str, int] = {}
    log = get_logger("agrovision.inspect")
    for ds in load_catalog():
        if ids and ds.get("id") not in ids:
            continue
        for record in inspeccionar_dataset(ds, config):
            append_jsonl(salida, record)
            total[record["estado"]] = total.get(record["estado"], 0) + 1
        log.info(
            "inspect_dataset",
            extra_fields={"dataset_id": ds.get("id"), "resumen": total},
        )
    print(f"Resumen inspect: {total} → {salida}")


if __name__ == "__main__":
    main()
