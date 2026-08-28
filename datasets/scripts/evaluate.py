"""Etapa Evaluate (sección 17) — métricas por clase y calibración.

Clasificación: macro-F1, balanced accuracy, precision/recall por clase,
matriz de confusión, ECE/Brier (RF-12, RF-14). Reporte JSON + CSV + HTML.

Uso:
    python evaluate.py --predicciones predictions.jsonl [--clases 5]
"""

from __future__ import annotations

import argparse
import csv
import json
from collections import defaultdict
from pathlib import Path

from common import REPORTS_DIR, get_logger, read_jsonl

import numpy as np  # noqa: E402

log = get_logger("agrovision.evaluate")


def _ece(y_true: np.ndarray, probs: np.ndarray, bins: int = 10) -> float:
    confs = probs.max(axis=1)
    accs = probs.argmax(axis=1) == y_true
    bordes = np.linspace(0.0, 1.0, bins + 1)
    ece, pesos = 0.0, 0.0
    for i in range(bins):
        mascara = (confs > bordes[i]) & (confs <= bordes[i + 1])
        if mascara.sum() == 0:
            continue
        conf_media = float(confs[mascara].mean())
        acc_media = float(accs[mascara].mean())
        ece += mascara.sum() * abs(acc_media - conf_media)
        pesos += mascara.sum()
    return ece / max(pesos, 1)


def evaluar_clasificacion(y_true: np.ndarray, probs: np.ndarray, clases: list[str]) -> dict:
    from sklearn.metrics import (
        balanced_accuracy_score,
        confusion_matrix,
        f1_score,
        precision_recall_fscore_support,
    )

    y_pred = probs.argmax(axis=1)
    precision, recall, f1, apoyo = precision_recall_fscore_support(
        y_true, y_pred, labels=list(range(len(clases))), zero_division=0
    )
    matriz = confusion_matrix(y_true, y_pred, labels=list(range(len(clases))))
    por_clase = [
        {
            "clase": clases[i],
            "precision": round(float(precision[i]), 4),
            "recall": round(float(recall[i]), 4),
            "f1": round(float(f1[i]), 4),
            "soporte": int(apoyo[i]),
        }
        for i in range(len(clases))
    ]
    return {
        "macro_f1": round(float(f1_score(y_true, y_pred, average="macro", zero_division=0)), 4),
        "balanced_accuracy": round(
            float(balanced_accuracy_score(y_true, y_pred)), 4
        ),
        "ece": round(_ece(y_true, probs), 4),
        "brier": round(
            float(np.mean(np.sum((probs - np.eye(len(clases))[y_true]) ** 2, axis=1))), 4
        ),
        "confusion_matrix": matriz.tolist(),
        "por_clase": por_clase,
    }


def evaluar_deteccion(predicciones: list[dict], iou_umbral: float = 0.5) -> dict:
    """mAP50 simple con emparejamiento por IoU (sin torch)."""

    def iou(a: list[float], b: list[float]) -> float:
        x1 = max(a[0], b[0])
        y1 = max(a[1], b[1])
        x2 = min(a[0] + a[2], b[0] + b[2])
        y2 = min(a[1] + a[3], b[1] + b[3])
        inter = max(0.0, x2 - x1) * max(0.0, y2 - y1)
        union = a[2] * a[3] + b[2] * b[3] - inter
        return inter / union if union > 0 else 0.0

    por_clase: dict[str, list[tuple[float, bool]]] = defaultdict(list)
    for item in predicciones:
        for pred in item.get("predicciones", []):
            clase = pred.get("class", "unknown")
            mejor_iou = max(
                (iou(pred.get("bbox", [0, 0, 0, 0]), gt.get("bbox", [0, 0, 0, 0])) for gt in item.get("etiquetas", [])),
                default=0.0,
            )
            por_clase[clase].append((float(pred.get("confianza", 0.0)), mejor_iou >= iou_umbral))
    aps = {}
    for clase, items in por_clase.items():
        items.sort(key=lambda t: -t[0])
        aciertos, total_gt = 0, len(items)
        precisiones, recalls = [], []
        for i, (_, ok) in enumerate(items, start=1):
            aciertos += int(ok)
            precisiones.append(aciertos / i)
            recalls.append(aciertos / max(total_gt, 1))
        if not precisiones:
            continue
        aps[clase] = round(float(np.mean(precisiones)), 4)
    return {"map50": round(float(np.mean(list(aps.values()))) if aps else 0.0, 4), "por_clase": aps}


def escribir_reportes(metricas: dict, prefijo: str = "evaluation") -> dict:
    base = REPORTS_DIR / prefijo
    base.mkdir(parents=True, exist_ok=True)
    (base / "metrics.json").write_text(
        json.dumps(metricas, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    por_clase = metricas.get("por_clase", [])
    if por_clase:
        with open(base / "metrics.csv", "w", newline="", encoding="utf-8") as fh:
            writer = csv.DictWriter(fh, fieldnames=list(por_clase[0].keys()))
            writer.writeheader()
            writer.writerows(por_clase)
    html = [
        "<html><head><meta charset='utf-8'><title>AgroVision - Evaluación</title></head><body>",
        "<h1>Reporte de evaluación AgroVision</h1>",
        "<pre>" + json.dumps(metricas, indent=2, ensure_ascii=False) + "</pre>",
        "</body></html>",
    ]
    (base / "report.html").write_text("\n".join(html), encoding="utf-8")
    return {"json": str(base / "metrics.json"), "csv": str(base / "metrics.csv"), "html": str(base / "report.html")}


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate — métricas y calibración.")
    parser.add_argument("--predicciones", default=None, help="JSONL y_true/probs/clases.")
    parser.add_argument("--salida", default="evaluation")
    args = parser.parse_args()

    if not args.predicciones:
        print("Debe indicar --predicciones (JSONL con y_true, probs, clases).")
        raise SystemExit(1)
    registros = list(read_jsonl(Path(args.predicciones)))
    clases = registros[0]["clases"] if registros else []
    y_true = np.array([r["y_true"] for r in registros])
    probs = np.array([r["probs"] for r in registros])
    metricas = evaluar_clasificacion(y_true, probs, clases)
    rutas = escribir_reportes(metricas, args.salida)
    log.info("evaluate_result", extra_fields={**metricas, "rutas": rutas})
    print(json.dumps({**metricas, "rutas": rutas}, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
