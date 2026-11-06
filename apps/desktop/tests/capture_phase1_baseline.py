"""Capturas reales de Tk y respaldo de prueba de etapa 1; no usar datos privados."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import shutil
import sys
import tempfile
import time
from pathlib import Path

from PIL import ImageGrab

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from smart_uni.core import SmartUniService, seed_demo
from smart_uni.student_data import StudentSpaceService, seed_student_demo
from smart_uni.ui import SmartUniApp


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def screenshot(app: SmartUniApp, path: Path) -> None:
    app.deiconify()
    app.update_idletasks()
    app.update()
    time.sleep(0.45)
    x, y = app.winfo_rootx(), app.winfo_rooty()
    width, height = app.winfo_width(), app.winfo_height()
    if width < 500 or height < 400:
        raise RuntimeError(f"Tamaño de ventana inesperado: {width}x{height}")
    image = ImageGrab.grab(bbox=(x, y, x + width, y + height))
    if image.size != (width, height):
        raise RuntimeError(f"Captura incompleta: {image.size} != {(width, height)}")
    image.save(path, format="PNG")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="smartuni-phase1-") as temp:
        data_path = Path(temp) / "data.json"
        service = SmartUniService(data_path)
        seed_demo(service)
        seed_student_demo(StudentSpaceService(service))
        app = SmartUniApp(service)
        try:
            screenshot(app, output / "01_acceso.png")
            app.user = service.authenticate("demo@smartuni.edu", "Demo1234!")
            if app.user is None:
                raise AssertionError("No fue posible iniciar sesión en la demo")
            screens = [
                ("02_panel.png", app.show_dashboard),
                ("03_tareas.png", lambda: app.show_student_space("Tareas")),
                ("04_material.png", lambda: app.show_student_space("Material")),
                ("05_apuntes.png", lambda: app.show_student_space("Apuntes")),
            ]
            for filename, show in screens:
                show()
                screenshot(app, output / filename)
        finally:
            app.destroy()
        # Contiene únicamente la cuenta y contenidos de demostración, nunca datos reales.
        shutil.copy2(data_path, output / "respaldo_demo_sintetico.json")

    expected = [
        "01_acceso.png", "02_panel.png", "03_tareas.png",
        "04_material.png", "05_apuntes.png", "respaldo_demo_sintetico.json",
    ]
    hashes = {name: sha256(output / name) for name in expected}
    manifest = {
        "scope": "SMART UNI 2.0 - 1.3 - solo datos sinteticos",
        "commit": os.environ.get("GITHUB_SHA", "ejecucion-local"),
        "os": platform.platform(),
        "python": sys.version.split()[0],
        "display": "Tkinter/Pillow ImageGrab",
        "files_sha256": hashes,
        "backup_restore": "validado por test_synthetic_backup_can_be_restored (suite unittest)",
    }
    (output / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(manifest, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
