"""Preparamos el icono de Windows utilizando el birrete original de SMART UNI.

Este archivo solamente genera el formato .ico. No modifica las pantallas.
Necesita Pillow: python -m pip install pillow
"""

from pathlib import Path
from PIL import Image


def main():
    base = Path(__file__).resolve().parent
    original = base / "previews" / "00_isotipo_smart_uni.png"
    destination = base / "smart_uni.ico"

    if not original.exists():
        raise FileNotFoundError("Falta el icono original SMART UNI")

    with Image.open(original) as source:
        image = source.convert("RGBA")
        canvas = Image.new("RGBA", (256, 256), (0, 0, 0, 0))
        image.thumbnail((236, 236), Image.Resampling.LANCZOS)
        x = (256 - image.width) // 2
        y = (256 - image.height) // 2
        canvas.paste(image, (x, y), image)
        canvas.save(destination, format="ICO", sizes=[
            (16, 16), (24, 24), (32, 32), (48, 48),
            (64, 64), (128, 128), (256, 256),
        ])
    print("Icono Windows generado:", destination)


if __name__ == "__main__":
    main()
