# -*- coding: utf-8 -*-
"""Genera los GIF animados de los manuales de usuario (apps/frontend-web/media-ayuda).

Uso:  .venv\\Scripts\\python.exe scripts/gen_ayuda_gifs.py
Cada GIF encadena capturas reales de la aplicación con transiciones suaves y una
franja inferior que indica el paso (Paso N de M — descripción).
"""
from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

BASE = Path(__file__).resolve().parents[1] / "apps" / "frontend-web" / "media-ayuda"
WIDTH = 1000
FONT_PATH = "C:/Windows/Fonts/arial.ttf"
DURATION = 1500          # ms por frame
FADE_STEPS = 6           # frames de transición
FADE_DURATION = 60       # ms por paso de transición

GIFS = {
    # nombre → [(archivo, descripción), ...]
    "gif-login.gif": [
        ("login.png", "Paso 1 — Ingrese con su email y contraseña o use una cuenta demo"),
        ("inicio.png", "Paso 2 — Al entrar verá el panel de Inicio de AgroIA"),
    ],
    "gif-registro-finca.gif": [
        ("admin-menu.png", "Paso 1 — Menú ⚙️ Administración → 🏡 Registrar finca"),
        ("registrar-finca-1.png", "Paso 2 — Sección 1: información básica del predio"),
        ("registrar-finca-2.png", "Paso 3 — Sección 2: ubicación GPS, mapa o enlace"),
        ("registrar-finca-3.png", "Paso 4 — Sección 3: características del suelo y del lote"),
        ("fincas.png", "Paso 5 — La finca queda registrada y aparece en el listado"),
    ],
    "gif-analisis.gif": [
        ("inicio.png", "Paso 1 — Elija la finca de análisis desde el Inicio"),
        ("recomendaciones.png", "Paso 2 — Seleccione cultivo (opcional) y presupuesto y haga clic en 🧪 Analizar suelo"),
        ("recomendaciones-resultado.png", "Paso 3 — Revise el diagnóstico: clasificación, confianza, acciones y plan"),
    ],
    "gif-precios.gif": [
        ("admin-menu.png", "Paso 1 — Menú ⚙️ Administración → 💰 Administrar insumos"),
        ("insumos.png", "Paso 2 — Actualice el precio COP/kg de cada insumo y guarde"),
    ],
    "gif-ayuda.gif": [
        ("login.png", "En cualquier pantalla encontrará el menú ❓ Ayuda arriba a la derecha"),
        ("admin-menu.png", "Su manual de usuario se abre según su rol (aquí: Administrador)"),
    ],
}


def _caption_bar(img: Image.Image, texto: str, font: ImageFont.FreeTypeFont, altura: int) -> Image.Image:
    lienzo = Image.new("RGB", (img.width, img.height + altura), (23, 56, 31))
    lienzo.paste(img, (0, 0))
    d = ImageDraw.Draw(lienzo)
    d.rectangle([0, img.height, img.width, img.height + altura], fill=(23, 56, 31))
    d.text((22, img.height + (altura - font.size) // 2 - 4), texto, fill=(240, 255, 242), font=font)
    return lienzo


def _cargar(archivo: str) -> Image.Image:
    img = Image.open(BASE / archivo).convert("RGB")
    proporcional = WIDTH / img.width
    alto = round(img.height * proporcional)
    return img.resize((WIDTH, alto), Image.LANCZOS)


def main() -> None:
    BASE.mkdir(parents=True, exist_ok=True)
    font = ImageFont.truetype(FONT_PATH, 26)
    for nombre, pasos in GIFS.items():
        frames: list[Image.Image] = []
        duraciones: list[int] = []
        total = len(pasos)
        for idx, (archivo, texto) in enumerate(pasos, start=1):
            base = _caption_bar(_cargar(archivo), f"Paso {idx} de {total} — {texto}", font, 62)
            frames.append(base)
            duraciones.append(DURATION)
            # transición de fundido hacia el siguiente frame
            if idx < total:
                siguiente = _caption_bar(
                    _cargar(pasos[idx][0]),
                    f"Paso {idx + 1} de {total} — {pasos[idx][1]}",
                    font,
                    62,
                )
                for t in range(1, FADE_STEPS):
                    mezcla = Image.blend(base, siguiente, t / FADE_STEPS)
                    frames.append(mezcla)
                    duraciones.append(FADE_DURATION)
        frames[0].save(
            BASE / nombre,
            save_all=True,
            append_images=frames[1:],
            duration=duraciones,
            loop=0,
            optimize=True,
        )
        print(f"OK {nombre} — {len(frames)} frames")


if __name__ == "__main__":
    main()
