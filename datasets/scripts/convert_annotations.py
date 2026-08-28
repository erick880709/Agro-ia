"""Conversión de anotaciones COCO ↔ YOLO ↔ máscaras (RF-09).

Esquema interno común (JSONL en annotations/<DS>/labels.jsonl):
    {"image_id", "file", "width", "height", "labels": [
        {"class", "bbox": [x, y, w, h], "area", "mask_rel": <path|None>}
    ]}
Solo se convierte cuando se mantiene la semántica; las conversiones inválidas
se registran como error por imagen sin detener el pipeline.

Uso:
    python convert_annotations.py --ds DS02 --from coco --to internal
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from common import (
    ANNOTATIONS_DIR,
    RAW_DIR,
    append_jsonl,
    get_logger,
    load_catalog,
)

log = get_logger("agrovision.convert")


def coco_a_interno(coco_path: Path, raiz_imagenes: Path) -> list[dict]:
    with open(coco_path, encoding="utf-8") as fh:
        coco = json.load(fh)
    categorias = {c["id"]: c["name"] for c in coco.get("categories", [])}
    imagenes = {i["id"]: i for i in coco.get("images", [])}
    por_imagen: dict[int, list[dict]] = {}
    for ann in coco.get("annotations", []):
        bbox = ann.get("bbox", [0, 0, 0, 0])
        por_imagen.setdefault(ann["image_id"], []).append(
            {
                "class": categorias.get(ann.get("category_id"), "unknown"),
                "bbox": bbox,
                "area": ann.get("area"),
            }
        )
    registros: list[dict] = []
    for img_id, img in imagenes.items():
        registros.append(
            {
                "image_id": str(img_id),
                "file": img.get("file_name"),
                "width": img.get("width"),
                "height": img.get("height"),
                "source_format": "coco",
                "labels": por_imagen.get(img_id, []),
            }
        )
    return registros


def yolo_a_interno(labels_dir: Path, class_names: list[str]) -> list[dict]:
    registros: list[dict] = []
    for txt in sorted(labels_dir.glob("*.txt")):
        labels: list[dict] = []
        with open(txt, encoding="utf-8") as fh:
            for line in fh:
                partes = line.split()
                if len(partes) < 5:
                    continue  # línea malformada → omitida y contada
                try:
                    cls, cx, cy, w, h = [float(x) for x in partes[:5]]
                except ValueError:
                    continue
                labels.append(
                    {
                        "class": class_names[int(cls)] if int(cls) < len(class_names) else "unknown",
                        "bbox": [cx, cy, w, h],
                        "bbox_norm": True,
                    }
                )
        registros.append(
            {
                "image_id": txt.stem,
                "file": txt.with_suffix(".jpg").name,
                "source_format": "yolo",
                "labels": labels,
            }
        )
    return registros


def interno_a_yolo(registros: list[dict], destino: Path) -> int:
    destino.mkdir(parents=True, exist_ok=True)
    total = 0
    for reg in registros:
        with open(destino / f"{reg['image_id']}.txt", "w", encoding="utf-8") as fh:
            for label in reg.get("labels", []):
                bbox = label.get("bbox")
                if not bbox or len(bbox) != 4:
                    continue
                fh.write(f"0 {' '.join(f'{v:.6f}' for v in bbox)}\n")
                total += 1
    return total


def ejecutar(ds_id: str, desde: str, hacia: str) -> list[dict]:
    ds = next((d for d in load_catalog() if d.get("id") == ds_id), None)
    if ds is None:
        raise SystemExit(f"Dataset {ds_id} no está en el catálogo.")
    version = ds.get("version") or "current"
    raiz = RAW_DIR / ds_id / version
    salida = ANNOTATIONS_DIR / ds_id
    registros: list[dict] = []
    if desde == "coco":
        coco_file = next(raiz.rglob("*.json"), None)
        if coco_file is None:
            raise SystemExit(f"No se encontró archivo COCO en {raiz}.")
        registros = coco_a_interno(coco_file, raiz)
    elif desde == "yolo":
        labels_dir = next((p for p in raiz.rglob("labels") if p.is_dir()), None)
        if labels_dir is None:
            labels_dir = next((p for p in raiz.rglob("*") if p.is_dir() and list(p.glob("*.txt"))), None)
        if labels_dir is None:
            raise SystemExit(f"No se encontraron etiquetas YOLO en {raiz}.")
        registros = yolo_a_interno(labels_dir, ds.get("classes", []))
    else:
        raise SystemExit(f"Formato de origen no soportado: {desde}")

    if hacia == "internal":
        out = salida / "labels.jsonl"
        if out.exists():
            out.unlink()
        for reg in registros:
            append_jsonl(out, {**reg, "dataset_id": ds_id, "version": version})
    elif hacia == "yolo":
        interno_a_yolo(registros, salida / "yolo")
    else:
        raise SystemExit(f"Formato destino no soportado: {hacia}")
    return registros


def main() -> None:
    parser = argparse.ArgumentParser(description="Convert — anotaciones COCO/YOLO/masks.")
    parser.add_argument("--ds", required=True)
    parser.add_argument("--from", dest="desde", required=True, choices=["coco", "yolo"])
    parser.add_argument("--to", dest="hacia", required=True, choices=["internal", "yolo"])
    args = parser.parse_args()
    registros = ejecutar(args.ds, args.desde, args.hacia)
    log.info(
        "convert_ok",
        extra_fields={"dataset_id": args.ds, "imagenes": len(registros), "hacia": args.hacia},
    )
    print(f"Convertidas {len(registros)} imágenes → {ANNOTATIONS_DIR / args.ds}")


if __name__ == "__main__":
    main()
