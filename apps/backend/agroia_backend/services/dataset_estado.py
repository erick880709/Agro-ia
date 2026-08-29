"""Estado del pipeline de datasets AgroVision (RQ de trazabilidad, v6 §2.5).

Resumen read-only del árbol `datasets/`: manifest, metadata JSONL, carpetas
de ingesta/curación y paquetes de modelos. Sin dependencias nuevas: solo
stdlib (el backend no incluye PyYAML, el manifest se inspecciona por patrón).
"""

from __future__ import annotations

import json
import re
from pathlib import Path


def _contar_jsonl(ruta: Path) -> int:
    if not ruta.is_file():
        return 0
    try:
        with open(ruta, encoding="utf-8") as fh:
            return sum(1 for linea in fh if linea.strip())
    except OSError:
        return 0


def _ultimo_estado_discover(raiz: Path) -> dict:
    """Estado más reciente por dataset según metadata/discovery.jsonl."""
    resultado: dict = {}
    ruta = raiz / "metadata" / "discovery.jsonl"
    if not ruta.is_file():
        return resultado
    try:
        with open(ruta, encoding="utf-8") as fh:
            for linea in fh:
                linea = linea.strip()
                if not linea:
                    continue
                try:
                    reg = json.loads(linea)
                except json.JSONDecodeError:
                    continue
                ds_id = reg.get("dataset_id")
                if ds_id:
                    resultado[ds_id] = reg.get("estado")
    except OSError:
        pass
    return resultado


def _modelos_empaquetados(raiz: Path) -> list[dict]:
    modelos = []
    base = raiz / "models"
    if not base.is_dir():
        return modelos
    for manifest in sorted(base.glob("*/manifest.json")):
        nombre = manifest.parent.name
        version = manifest.parent.parent.name
        try:
            data = json.loads(manifest.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            data = {}
        modelos.append(
            {
                "nombre": data.get("model_name", nombre),
                "version": data.get("version", version),
                "sha256": data.get("sha256"),
                "datasets": [d.get("dataset_id") for d in data.get("datasets", [])],
            }
        )
    return modelos


def estado_datasets(raiz: Path) -> dict:
    if not raiz.is_dir():
        return {
            "disponible": False,
            "ruta": str(raiz),
            "detalle": "Directorio datasets/ no montado en este despliegue.",
        }
    manifest = raiz / "manifest" / "datasets.yaml"
    datasets_declarados = 0
    if manifest.is_file():
        try:
            texto = manifest.read_text(encoding="utf-8")
            datasets_declarados = len(re.findall(r"^\s*-\s+id:\s*\S+", texto, re.MULTILINE))
        except OSError:
            pass
    metadata = raiz / "metadata"
    raw = raiz / "raw"
    curated = raiz / "curated" / "classification"
    return {
        "disponible": True,
        "ruta": str(raiz),
        "manifest": {
            "presente": manifest.is_file(),
            "datasets_declarados": datasets_declarados,
        },
        "metadata": {
            "discovery": _contar_jsonl(metadata / "discovery.jsonl"),
            "downloads": _contar_jsonl(metadata / "downloads.jsonl"),
            "inspection": _contar_jsonl(metadata / "inspection.jsonl"),
            "duplicates": _contar_jsonl(metadata / "duplicates.jsonl"),
            "images": _contar_jsonl(metadata / "images.jsonl"),
            "lineage": _contar_jsonl(metadata / "lineage.jsonl"),
        },
        "fuentes": {
            "estado_discover": _ultimo_estado_discover(raiz),
            "raw_datasets": len([p for p in raw.glob("*") if p.is_dir()]) if raw.is_dir() else 0,
            "quarantine_datasets": len(
                [p for p in (raiz / "quarantine").glob("*") if p.is_dir()]
            ) if (raiz / "quarantine").is_dir() else 0,
        },
        "curacion": {
            "train": sum(1 for _ in curated.glob("train/*/*/*")) if curated.is_dir() else 0,
            "val": sum(1 for _ in curated.glob("val/*/*/*")) if curated.is_dir() else 0,
            "test": sum(1 for _ in curated.glob("test/*/*/*")) if curated.is_dir() else 0,
            "normalized_datasets": len(
                [p for p in (raiz / "normalized").glob("*") if p.is_dir()]
            ) if (raiz / "normalized").is_dir() else 0,
        },
        "modelos": _modelos_empaquetados(raiz),
    }
