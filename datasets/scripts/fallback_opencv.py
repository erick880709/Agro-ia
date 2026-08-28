"""Fallback OpenCV + quality gate (sección 14) — CLI standalone.

Reutiliza el motor de visión del backend (agroia_backend.services.
vision_fallback) para que datasets y API compartan exactamente las mismas
reglas. Soporta cv2 o numpy puro de forma transparente.

Uso:
    python fallback_opencv.py <imagen.jpg> [--crop coffee] [--json]
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
for _ruta in (REPO_ROOT / "apps" / "backend", REPO_ROOT / "apps" / "shared"):
    if str(_ruta) not in sys.path:
        sys.path.insert(0, str(_ruta))

from agroia_backend.services.vision_fallback import diagnosticar  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Fallback de visión tradicional AgroVision (OpenCV/numpy)."
    )
    parser.add_argument("imagen", help="Ruta a la imagen a diagnosticar.")
    parser.add_argument("--crop", default=None, help="Cultivo sugerido (coffee/cacao).")
    parser.add_argument("--json", action="store_true", help="Salida JSON en una línea.")
    args = parser.parse_args()

    contenido = Path(args.imagen).read_bytes()
    resultado = diagnosticar(contenido, crop_hint=args.crop)
    if args.json:
        print(json.dumps(resultado, ensure_ascii=False))
    else:
        print(json.dumps(resultado, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
