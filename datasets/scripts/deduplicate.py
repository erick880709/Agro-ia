"""Etapa Deduplicate (11.4) — exactos por SHA-256 y similares por pHash.

Nunca borra físicamente del raw: registra el ganador (`keep`) y los
descartados con `duplicate_of` en metadata/duplicates.jsonl.

Uso:
    python deduplicate.py [--ids DS01,DS02] [--phash-threshold 8]
"""

from __future__ import annotations

import argparse
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

from common import (
    METADATA_DIR,
    RAW_DIR,
    append_jsonl,
    get_logger,
    hamming_distance,
    load_catalog,
    load_pipeline_config,
    phash,
    sha256_file,
)

import numpy as np  # noqa: E402

log = get_logger("agrovision.dedup")


def _cargar_imagen(path: Path) -> np.ndarray:
    try:
        from PIL import Image  # type: ignore

        with Image.open(path) as img:
            return np.asarray(img.convert("RGB"))
    except Exception:
        return np.zeros((1, 1, 3), dtype=np.uint8)


def deduplicar_dataset(ds: dict, threshold: int) -> list[dict]:
    version = ds.get("version") or "current"
    raiz = RAW_DIR / ds.get("id") / version
    if not raiz.exists():
        return []
    archivos = [p for p in sorted(raiz.rglob("*")) if p.is_file()]
    exactos: dict[str, list[Path]] = defaultdict(list)
    for path in archivos:
        exactos[sha256_file(path)].append(path)
    registros: list[dict] = []
    ganadores: list[Path] = []
    for group in exactos.values():
        ganador = group[0]
        ganadores.append(ganador)
        for dup in group[1:]:
            registros.append(
                {
                    "dataset_id": ds.get("id"),
                    "version": version,
                    "archivo": str(dup.relative_to(raiz)),
                    "duplicate_of": str(ganador.relative_to(raiz)),
                    "motivo": "hash_exacto_sha256",
                    "decision": "discard",
                }
            )
    # Duplicados visuales entre ganadores (pHash).
    hashes = {p: phash(_cargar_imagen(p)) for p in ganadores}
    revisados: set[Path] = set()
    for i, p in enumerate(ganadores):
        if p in revisados:
            continue
        for q in ganadores[i + 1 :]:
            if q in revisados or p == q:
                continue
            if hamming_distance(hashes[p], hashes[q]) <= threshold:
                registros.append(
                    {
                        "dataset_id": ds.get("id"),
                        "version": version,
                        "archivo": str(q.relative_to(raiz)),
                        "duplicate_of": str(p.relative_to(raiz)),
                        "motivo": f"perceptual_phash_{threshold}",
                        "decision": "discard",
                    }
                )
                revisados.add(q)
    for reg in registros:
        reg["registrado_en"] = datetime.now(timezone.utc).isoformat()
    return registros


def main() -> None:
    parser = argparse.ArgumentParser(description="Dedup — hashes exactos y perceptuales.")
    parser.add_argument("--ids", default="", help="IDs separados por coma.")
    parser.add_argument("--phash-threshold", type=int, default=None)
    args = parser.parse_args()

    config = load_pipeline_config()
    threshold = args.phash_threshold
    if threshold is None:
        threshold = config.get("dedup", {}).get("phash_threshold", 8)
    ids = {s.strip().upper() for s in args.ids.split(",") if s.strip()}
    salida = METADATA_DIR / "duplicates.jsonl"
    total = 0
    for ds in load_catalog():
        if ids and ds.get("id") not in ids:
            continue
        for record in deduplicar_dataset(ds, threshold):
            append_jsonl(salida, record)
            total += 1
        log.info(
            "dedup_dataset",
            extra_fields={"dataset_id": ds.get("id"), "duplicados": total},
        )
    print(f"Duplicados registrados: {total} → {salida}")


if __name__ == "__main__":
    main()
