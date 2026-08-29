"""Etapa Split (11.8, sección 16) — partición sin fuga (No leakage).

La unidad de partición es un grupo biológico o de captura, no una imagen.
Prioridad: farm_id > plant_id > leaf_id. source_url/dataset_id son constantes
por dataset y se reservan para trazabilidad (no como grupo, evitaría
particionar). Cuando no existe metadata de grupo (caso común en raw), se
agrupan primero los duplicados visuales por pHash (sección 16) y se
particiona por clusters, nunca separando imágenes casi idénticas entre
train y test.
La asignación de grupos a splits es greedy y estratificada por clase.

Uso:
    python split.py [--ids DS01,DS02] [--ratios 0.70,0.15,0.15] [--seed 42]
"""

from __future__ import annotations

import argparse
import json
import random
import shutil
from collections import defaultdict
from pathlib import Path

from common import (
    CURATED_DIR,
    METADATA_DIR,
    NORMALIZED_DIR,
    get_logger,
    hamming_distance,
    load_catalog,
    load_pipeline_config,
    phash,
    read_jsonl,
)

import numpy as np  # noqa: E402

log = get_logger("agrovision.split")

_GROUP_KEYS = ("farm_id", "plant_id", "leaf_id")


def _cargar(path: Path) -> np.ndarray:
    try:
        from PIL import Image  # type: ignore

        with Image.open(path) as img:
            return np.asarray(img.convert("RGB"))
    except Exception:
        return np.zeros((1, 1, 3), dtype=np.uint8)


def _clusters_por_phash(archivos: list[Path], threshold: int) -> list[list[Path]]:
    """Agrupa imágenes visualmente cercanas para no separarlas entre splits."""
    buckets: list[tuple[int, list[Path]]] = []
    for path in archivos:
        valor = phash(_cargar(path))
        for hash_base, grupo in buckets:
            if hamming_distance(hash_base, valor) <= threshold:
                grupo.append(path)
                break
        else:
            buckets.append((valor, [path]))
    return [grupo for _, grupo in buckets]


def _asignar_grupos(
    grupos: list[tuple[str, dict[str, int]]], ratios: list[float], seed: int
) -> dict[str, str]:
    """Greedy estratificado por clase: cada grupo va al split con mayor
    déficit agregado POR CLASE (así ninguna clase queda fuera de un split);
    desempata por déficit total y luego aleatorio.
    """
    nombres = ["train", "val", "test"]
    contadores: dict[str, dict[str, int]] = {s: defaultdict(int) for s in nombres}
    contador_total: dict[str, int] = {s: 0 for s in nombres}
    totales_por_clase: dict[str, int] = defaultdict(int)
    for _, clases in grupos:
        for clase, n in clases.items():
            totales_por_clase[clase] += n
    total_imagenes = sum(totales_por_clase.values()) or 1
    randomizer = random.Random(seed)
    asignacion: dict[str, str] = {}
    orden = sorted(grupos, key=lambda item: -sum(item[1].values()))
    for nombre_grupo, clases in orden:
        n_grupo = sum(clases.values())
        mejor, mejor_deficit, mejor_total = None, -float("inf"), -float("inf")
        for split, ratio in zip(nombres, ratios):
            # Déficit relativo por clase: 0 cuando el split ya alcanzó su
            # proporción objetivo para todas las clases.
            deficit_clase = sum(
                max(
                    0.0,
                    1.0
                    - (contadores[split].get(clase, 0) + clases.get(clase, 0))
                    / max(total * ratio, 1e-9),
                )
                for clase, total in totales_por_clase.items()
            )
            deficit_total = max(
                0.0,
                1.0 - (contador_total[split] + n_grupo) / max(total_imagenes * ratio, 1e-9),
            )
            if (
                deficit_clase > mejor_deficit
                or (deficit_clase == mejor_deficit and deficit_total > mejor_total)
                or (
                    deficit_clase == mejor_deficit
                    and deficit_total == mejor_total
                    and randomizer.random() < 0.5
                )
            ):
                mejor, mejor_deficit, mejor_total = split, deficit_clase, deficit_total
        mejor = mejor or "train"
        asignacion[nombre_grupo] = mejor
        contador_total[mejor] += n_grupo
        for clase, n in clases.items():
            contadores[mejor][clase] += n
    return asignacion


def partir_dataset(ds_id: str, ratios: list[float], seed: int, phash_threshold: int = 8) -> dict:
    raiz = NORMALIZED_DIR / ds_id
    if not raiz.exists():
        return {"dataset_id": ds_id, "estado": "sin_datos_normalizados"}
    # 1. Imágenes por clase.
    archivos: list[tuple[str, Path]] = []
    for clase_dir in sorted(p for p in raiz.iterdir() if p.is_dir()):
        if clase_dir.name == "multispectral":
            continue
        for archivo in sorted(clase_dir.glob("*")):
            if archivo.is_file():
                archivos.append((clase_dir.name, archivo))
    if not archivos:
        return {"dataset_id": ds_id, "estado": "sin_imagenes"}
    # 2. Grupos: metadata real si existe; si no, clusters por pHash.
    meta = {
        str(r.get("normalized_path")): r
        for r in read_jsonl(METADATA_DIR / "images.jsonl")
        if r.get("dataset_id") == ds_id
    }

    def registro_de(path: Path) -> dict:
        return meta.get(str(path.relative_to(NORMALIZED_DIR)), {})

    hay_grupos_reales = any(
        registro_de(p).get(k) for _, p in archivos for k in _GROUP_KEYS
    )
    if hay_grupos_reales:
        por_grupo: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
        for clase, path in archivos:
            registro = registro_de(path)
            clave = next(
                (f"{k}:{registro[k]}" for k in _GROUP_KEYS if registro.get(k)),
                "dataset_id",
            )
            por_grupo[clave][clase] += 1
        grupos: list[tuple[str, dict[str, int]]] = [(k, dict(v)) for k, v in por_grupo.items()]
        grupo_de: dict[Path, str] = {}
        for clase, path in archivos:
            registro = registro_de(path)
            grupo_de[path] = next(
                (f"{k}:{registro[k]}" for k in _GROUP_KEYS if registro.get(k)),
                "dataset_id",
            )
    else:
        clusters = _clusters_por_phash([p for _, p in archivos], phash_threshold)
        grupos = []
        grupo_de = {}
        for i, cluster in enumerate(clusters):
            conteo: dict[str, int] = defaultdict(int)
            for path in cluster:
                clase = next(c for c, p in archivos if p == path)
                conteo[clase] += 1
                grupo_de[path] = f"cluster_{i}"
            grupos.append((f"cluster_{i}", dict(conteo)))
    # 3. Asignación greedy estratificada.
    asignacion = _asignar_grupos(grupos, ratios, seed)
    # 4. Copia física y manifest.
    manifest: list[dict] = []
    for clase, path in archivos:
        split = asignacion.get(grupo_de.get(path, "dataset_id"), "train")
        destino = CURATED_DIR / "classification" / split / ds_id / clase
        destino.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, destino / path.name)
        manifest.append(
            {
                "dataset_id": ds_id,
                "split": split,
                "class": clase,
                "file": str((destino / path.name).relative_to(CURATED_DIR)),
                "group": grupo_de.get(path, "dataset_id"),
            }
        )
    return {"dataset_id": ds_id, "estado": "ok", "registros": manifest}


def main() -> None:
    parser = argparse.ArgumentParser(description="Split — partición sin fuga.")
    parser.add_argument("--ids", default="", help="IDs separados por coma.")
    parser.add_argument("--ratios", default=None, help="p.ej. 0.70,0.15,0.15")
    parser.add_argument("--seed", type=int, default=None)
    args = parser.parse_args()

    config = load_pipeline_config()
    ratios = (
        [float(x) for x in args.ratios.split(",")]
        if args.ratios
        else config.get("splits", {}).get("default", [0.70, 0.15, 0.15])
    )
    seed = args.seed if args.seed is not None else config.get("splits", {}).get("seed", 42)
    threshold = config.get("dedup", {}).get("phash_threshold", 8)
    ids = {s.strip().upper() for s in args.ids.split(",") if s.strip()}
    for ds in load_catalog():
        if ids and ds.get("id") not in ids:
            continue
        resultado = partir_dataset(ds.get("id"), ratios, seed, threshold)
        registros = resultado.get("registros")
        if registros is not None:
            salida = CURATED_DIR / "classification" / f"manifest_{ds.get('id')}.json"
            salida.parent.mkdir(parents=True, exist_ok=True)
            salida.write_text(
                json.dumps(registros, indent=2, ensure_ascii=False),
                encoding="utf-8",
            )
        log.info(
            "split_dataset",
            extra_fields={
                "dataset_id": ds.get("id"),
                "estado": resultado.get("estado"),
                "total": len(registros or []),
            },
        )
        print(f"{ds.get('id')}: {resultado.get('estado')} ({len(registros or [])})")


if __name__ == "__main__":
    main()
