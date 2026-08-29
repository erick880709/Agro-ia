"""Etapa Train (sección 15) — clasificación/detección; segmentación soportada.

Backends:
- `sklearn`: HistGradientBoostingClassifier sobre features de color/textura.
  Es un baseline de smoke-test de pipeline, NO un modelo de producción
  (benchmark CPU explícito requerido antes de elegir producción, RNF-04).
- `torch`: MobileNetV3/EfficientNet con ImageFolder si torch está instalado.
La aumentación se aplica solo durante el entrenamiento (11.7), nunca se
escribe en raw.

Uso:
    python train.py --config ../configs/train_classification.yaml
    python train.py --backend sklearn --curated ../curated/classification
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

from common import (
    CONFIGS_DIR,
    CURATED_DIR,
    DATASETS_ROOT,
    MODELS_DIR,
    REPORTS_DIR,
    get_logger,
    load_yaml,
)

import numpy as np  # noqa: E402

log = get_logger("agrovision.train")


def _features(path: Path, size: int = 32) -> np.ndarray:
    """Color (histogramas HSV) + textura (desvío local de gris)."""
    try:
        from PIL import Image  # type: ignore

        with Image.open(path) as img:
            rgb = np.asarray(img.convert("RGB").resize((size, size)))
    except Exception:
        return np.zeros(32 * 3 + size * size)
    rgb = rgb.astype(np.float64) / 255.0
    hist = np.concatenate([np.histogram(rgb[:, :, c], bins=32, range=(0, 1))[0] for c in range(3)])
    gris = rgb.mean(axis=2)
    grad0 = np.abs(np.diff(gris, axis=0))
    grad1 = np.abs(np.diff(gris, axis=1))
    alto = min(grad0.shape[0], grad1.shape[0])
    ancho = min(grad0.shape[1], grad1.shape[1])
    grad = grad0[:alto, :ancho] + grad1[:alto, :ancho]
    textura = np.resize(grad, size * size)
    return np.concatenate([hist / max(hist.sum(), 1), textura / max(textura.max(), 1)])


def cargar_curated(raiz: Path, split: str, etiquetas: list[str] | None = None) -> tuple[np.ndarray, np.ndarray, list[str]]:
    """Carga imágenes del split. `etiquetas` fija el vocabulario de clases
    (índices alineados entre splits; si el split no tiene una clase, no aporta
    filas de esa clase)."""
    carpetas = sorted(p for p in raiz.glob(f"{split}/*/*") if p.is_dir())
    etiquetas = list(etiquetas) if etiquetas is not None else sorted({p.name for p in carpetas})
    indice = {nombre: i for i, nombre in enumerate(etiquetas)}
    x, y, clases = [], [], []
    for carpeta in carpetas:
        if carpeta.name not in indice:
            continue
        etiqueta = indice[carpeta.name]
        for archivo in sorted(carpeta.glob("*")):
            if archivo.suffix.lower() not in {".jpg", ".jpeg", ".png", ".webp"}:
                continue
            x.append(_features(archivo))
            y.append(etiqueta)
            clases.append(archivo.name)
    return np.array(x), np.array(y), etiquetas


def _salida_modelos(config: dict) -> Path:
    base = Path(config.get("output_dir") or MODELS_DIR)
    if not base.is_absolute():
        base = (DATASETS_ROOT / base).resolve()
    return base


def entrenar_sklearn(config: dict, curated: Path) -> dict:
    from sklearn.ensemble import HistGradientBoostingClassifier

    x_train, y_train, etiquetas = cargar_curated(curated, "train")
    x_val, y_val, _ = cargar_curated(curated, "val", etiquetas)
    if len(etiquetas) < 2 or x_train.shape[0] == 0:
        return {"estado": "error", "detalle": "curated sin clases suficientes"}
    balance = config.get("balance")
    if balance not in ("balanced", None) and not isinstance(balance, dict):
        balance = None
    modelo = HistGradientBoostingClassifier(
        max_iter=200,
        random_state=config.get("seed", 42),
        class_weight=balance,
    )
    modelo.fit(x_train, y_train)
    version = f"sklearn-{datetime.now(timezone.utc):%Y%m%d-%H%M%S}"
    destino = _salida_modelos(config) / f"baseline-{version}"
    destino.mkdir(parents=True, exist_ok=True)
    import joblib

    joblib.dump(modelo, destino / "model.joblib")
    (destino / "classes.json").write_text(
        json.dumps({"classes": etiquetas, "config": config}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    if x_val.shape[0]:
        acc = float(modelo.score(x_val, y_val))
    else:
        acc = None
    return {
        "estado": "ok",
        "backend": "sklearn",
        "modelo_dir": str(destino),
        "clases": etiquetas,
        "accuracy_val": acc,
        "muestras_train": int(x_train.shape[0]),
    }


def entrenar_torch(config: dict, curated: Path) -> dict:
    import torch  # type: ignore

    from torch.utils.data import DataLoader  # type: ignore
    from torchvision import datasets, models, transforms  # type: ignore

    tam = config.get("image_size", 224)
    transform = transforms.Compose(
        [
            transforms.Resize((tam, tam)),
            transforms.RandomHorizontalFlip(p=0.5)
            if config.get("augmentation", {}).get("horizontal_flip", True)
            else transforms.Lambda(lambda x: x),
            transforms.ToTensor(),
            transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225]),
        ]
    )
    train_ds = datasets.ImageFolder(curated / "train", transform=transform)
    val_ds = datasets.ImageFolder(curated / "val", transform=transform)
    loader = DataLoader(train_ds, batch_size=config.get("batch_size", 32), shuffle=True)
    pesos = models.MobileNet_V3_Small_Weights.DEFAULT
    modelo = models.mobilenet_v3_small(weights=pesos)
    modelo.classifier[-1] = torch.nn.Linear(modelo.classifier[-1].in_features, len(train_ds.classes))
    opt = torch.optim.Adam(modelo.parameters(), lr=config.get("learning_rate", 1e-3))
    loss_fn = torch.nn.CrossEntropyLoss()
    modelo.train()
    for epoch in range(config.get("epochs", 10)):
        for batch, (imgs, labels) in enumerate(loader):
            opt.zero_grad()
            loss = loss_fn(modelo(imgs), labels)
            loss.backward()
            opt.step()
        log.info("torch_epoch", extra_fields={"epoch": epoch + 1, "loss": float(loss)})
    version = f"torch-{datetime.now(timezone.utc):%Y%m%d-%H%M%S}"
    destino = _salida_modelos(config) / f"vision-{version}"
    destino.mkdir(parents=True, exist_ok=True)
    torch.save(modelo.state_dict(), destino / "model.pt")
    (destino / "classes.json").write_text(
        json.dumps({"classes": train_ds.classes, "config": config}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return {
        "estado": "ok",
        "backend": "torch",
        "modelo_dir": str(destino),
        "clases": train_ds.classes,
        "muestras_train": len(train_ds),
        "muestras_val": len(val_ds),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Train — entrena modelos especializados.")
    parser.add_argument("--config", default=None, help="Ruta a config YAML.")
    parser.add_argument("--backend", default=None, choices=["auto", "sklearn", "torch"])
    parser.add_argument("--curated", default=None, help="Raíz curated/classification.")
    args = parser.parse_args()

    config = load_yaml(Path(args.config)) if args.config else load_yaml(
        CONFIGS_DIR / "train_classification.yaml"
    )
    curated = Path(args.curated) if args.curated else CURATED_DIR / "classification"
    backend = args.backend or config.get("backend", "auto")
    if backend == "auto":
        try:
            import torch  # type: ignore  # noqa: F401

            backend = "torch"
        except ImportError:
            backend = "sklearn"
    if backend == "torch":
        resultado = entrenar_torch(config, curated)
    else:
        resultado = entrenar_sklearn(config, curated)
    REPORTE = REPORTS_DIR / "training_report.json"
    REPORTE.parent.mkdir(parents=True, exist_ok=True)
    REPORTE.write_text(json.dumps(resultado, indent=2, ensure_ascii=False), encoding="utf-8")
    log.info("train_result", extra_fields=resultado)
    print(json.dumps(resultado, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
