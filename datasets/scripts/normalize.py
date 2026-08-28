"""Etapa Normalize (11.5, 11.6) — RGB, tamaños y taxonomía canónica.

- Convierte imágenes a RGB (máx. lado configurable) preservando original.
- Conserva aparte TIF multiespectral 16-bit.
- Mapea clases de origen a la taxonomía canónica (class_map.yaml) y
  conserva original_label. Label desconocido sin alias → quarantine (RF-08).
- Escribe metadata/images.jsonl y metadata/lineage.jsonl (RF-07).

Uso:
    python normalize.py [--ids DS01,DS02] [--max-side 512]
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
from pathlib import Path

from common import (
    METADATA_DIR,
    NORMALIZED_DIR,
    QUARANTINE_DIR,
    RAW_DIR,
    append_jsonl,
    get_logger,
    load_catalog,
    load_class_map,
    load_pipeline_config,
    sha256_file,
)

log = get_logger("agrovision.normalize")


def resolve_class(nombre: str, class_map: dict) -> str | None:
    """Mapea un nombre de clase original a la clase canónica."""
    nombre_n = nombre.strip().lower()
    aliases: dict = class_map.get("aliases", {})
    for canonical, sinónimos in aliases.items():
        for s in sinónimos:
            if str(s).strip().lower() == nombre_n:
                return canonical
    return nombre if nombre in class_map.get("taxonomy", {}).get("diagnostic_class", []) else None


def _imagen_original(archivo: Path, meta: dict, out_dir: Path, max_side: int) -> dict:
    from PIL import Image  # type: ignore

    destino = out_dir / archivo.name
    with Image.open(archivo) as img:
        is_multispectral = "tiff" in (img.format or "").lower() and img.mode not in ("RGB", "L")
        if is_multispectral:
            destino = out_dir / "multispectral" / archivo.name
            destino.parent.mkdir(parents=True, exist_ok=True)
            if not destino.exists():
                destino.write_bytes(archivo.read_bytes())
            meta["multispectral"] = True
            return meta
        rgb = img.convert("RGB")
        if max(rgb.size) > max_side:
            rgb.thumbnail((max_side, max_side))
        destino.parent.mkdir(parents=True, exist_ok=True)
        rgb.save(destino, format="JPEG", quality=92)
        meta["multispectral"] = False
    return meta


def normalizar_dataset(ds: dict, config: dict, class_map: dict) -> list[dict]:
    version = ds.get("version") or "current"
    raiz = RAW_DIR / ds.get("id") / version
    if not raiz.exists():
        return []
    max_side = config.get("normalize", {}).get("max_side", 512)
    registros: list[dict] = []
    # Clasificación por carpeta → clase (layout más común en estos datasets).
    carpetas = sorted({p.parent for p in raiz.rglob("*") if p.is_file()})
    for carpeta in carpetas:
        clase_origen = carpeta.name
        canonical = resolve_class(clase_origen, class_map)
        if canonical is None and len(carpetas) == 1:
            # Una sola carpeta no representa una clase → categoría genérica.
            canonical = "other"
        destino_clase = canonical or "quarantine_label"
        out_dir = NORMALIZED_DIR / ds.get("id") / destino_clase
        for archivo in sorted(carpeta.glob("*")):
            if not archivo.is_file() or archivo.suffix == ".part":
                continue
            if archivo.suffix.lower() not in {".jpg", ".jpeg", ".png", ".webp", ".tif", ".tiff", ".bmp"}:
                continue
            if canonical is None:
                q = QUARANTINE_DIR / ds.get("id") / version / archivo.name
                q.parent.mkdir(parents=True, exist_ok=True)
                import shutil

                shutil.move(str(archivo), str(q))
                registro = {
                    "dataset_id": ds.get("id"),
                    "version": version,
                    "archivo": str(archivo.name),
                    "original_label": clase_origen,
                    "estado": "quarantine",
                    "motivo": "label_desconocido_sin_alias",
                }
                registros.append(registro)
                continue
            meta = {
                "dataset_id": ds.get("id"),
                "version": version,
                "source_url": ds.get("source_url"),
                "license": ds.get("license"),
                "original_label": clase_origen,
                "canonical_label": canonical,
                "archivo": archivo.name,
                "ingesta": datetime.now(timezone.utc).isoformat(),
            }
            try:
                meta = _imagen_original(archivo, meta, out_dir, max_side)
            except Exception as exc:  # noqa: BLE001
                meta["estado"] = "quarantine"
                meta["motivo"] = f"normalizacion_fallida: {exc}"
                registros.append(meta)
                continue
            destino = out_dir / ("multispectral" if meta.get("multispectral") else "") / archivo.name
            if not meta.get("multispectral"):
                destino = out_dir / archivo.name
            meta["normalized_path"] = str(destino.relative_to(NORMALIZED_DIR))
            meta["sha256_normalized"] = sha256_file(destino)
            meta["estado"] = "ok"
            registros.append(meta)
            append_jsonl(
                METADATA_DIR / "lineage.jsonl",
                {
                    "dataset_id": ds.get("id"),
                    "version": version,
                    "raw": str(archivo.relative_to(raiz)),
                    "normalized": meta["normalized_path"],
                    "original_label": clase_origen,
                    "canonical_label": canonical,
                },
            )
    return registros


def main() -> None:
    parser = argparse.ArgumentParser(description="Normalize — RGB + taxonomía canónica.")
    parser.add_argument("--ids", default="", help="IDs separados por coma.")
    parser.add_argument("--max-side", type=int, default=None)
    args = parser.parse_args()

    config = load_pipeline_config()
    if args.max_side:
        config.setdefault("normalize", {})["max_side"] = args.max_side
    class_map = load_class_map()
    ids = {s.strip().upper() for s in args.ids.split(",") if s.strip()}
    salida = METADATA_DIR / "images.jsonl"
    resumen: dict[str, int] = {}
    for ds in load_catalog():
        if ids and ds.get("id") not in ids:
            continue
        for record in normalizar_dataset(ds, config, class_map):
            append_jsonl(salida, record)
            resumen[record["estado"]] = resumen.get(record["estado"], 0) + 1
        log.info(
            "normalize_dataset",
            extra_fields={"dataset_id": ds.get("id"), "resumen": resumen},
        )
    print(f"Resumen normalize: {resumen} → {salida}")


if __name__ == "__main__":
    main()
