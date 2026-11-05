"""Este script sirve para grabar el recorrido de SMART UNI en Linux.

Utilizamos Xvfb para abrir una pantalla virtual y FFmpeg para crear el video.
No es necesario ejecutar este script para abrir la aplicación en Windows.
"""

import os
import subprocess
import tempfile
import time
from pathlib import Path

from PIL import ImageGrab

from smart_uni.core import SmartUniService, seed_demo
from smart_uni.ui import SmartUniApp


ROOT = Path(__file__).resolve().parents[1]

# Preparamos una pantalla virtual para que se puedan grabar las ventanas.
os.environ['DISPLAY'] = ':97'
xvfb = subprocess.Popen(
    ['Xvfb', ':97', '-screen', '0', '1440x1000x24', '-nolisten', 'tcp'],
    stdout=subprocess.DEVNULL,
    stderr=subprocess.DEVNULL,
)

try:
    time.sleep(0.6)

    with tempfile.TemporaryDirectory() as folder:
        service = SmartUniService(Path(folder) / 'demo.json')
        seed_demo(service)

        app = SmartUniApp(service)
        app.geometry('1100x740+40+40')
        app.update()

        video = ROOT / 'video_demostrativo_smart_uni.mp4'
        ffmpeg = subprocess.Popen(
            [
                'ffmpeg',
                '-y',
                '-loglevel',
                'error',
                '-f',
                'x11grab',
                '-framerate',
                '12',
                '-video_size',
                '1100x740',
                '-i',
                ':97+40,40',
                '-c:v',
                'libx264',
                '-preset',
                'ultrafast',
                '-crf',
                '26',
                '-pix_fmt',
                'yuv420p',
                str(video),
            ],
            stdin=subprocess.PIPE,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
        )

        def hold(seconds):
            """Mantenemos cada pantalla visible el tiempo que necesita el video."""
            end = time.monotonic() + seconds

            while time.monotonic() < end:
                app.update()
                time.sleep(0.05)

        try:
            # Guardamos una imagen del inicio de sesión.
            ImageGrab.grab(
                bbox=(40, 40, 1140, 780),
                xdisplay=':97',
            ).save(ROOT / 'design/previews/05_app_login_real.png')
            hold(1.7)

            # Pasamos al registro y guardamos otra captura.
            app.show_register()
            app.update()
            ImageGrab.grab(
                bbox=(40, 40, 1140, 780),
                xdisplay=':97',
            ).save(ROOT / 'design/previews/06_app_registro_real.png')
            hold(2.1)

            # Regresamos al inicio e ingresamos la cuenta de demostración.
            app.show_login()
            app.update()

            entries = [
                widget
                for widget in app.winfo_children()[0].winfo_children()[0].winfo_children()
                if widget.winfo_class() == 'Entry'
            ]
            entries[0].insert(0, 'demo@smartuni.edu')
            entries[1].insert(0, 'Demo1234!')
            hold(1.3)

            buttons = [
                widget
                for widget in app.winfo_children()[0].winfo_children()[0].winfo_children()
                if widget.winfo_class() == 'Button'
            ]
            buttons[0].invoke()
            hold(2.6)

            # Ahora mostramos el panel, los cursos y las otras pantallas.
            ImageGrab.grab(
                bbox=(40, 40, 1140, 780),
                xdisplay=':97',
            ).save(ROOT / 'design/previews/07_app_panel_real.png')

            app.show_courses()
            app.update()
            ImageGrab.grab(
                bbox=(40, 40, 1140, 780),
                xdisplay=':97',
            ).save(ROOT / 'design/previews/08_app_cursos_real.png')
            hold(2.1)

            app.show_schedule()
            app.update()
            hold(2.1)

            app.show_announcements()
            app.update()
            hold(2.1)

            app.show_dashboard()
            app.update()
            hold(1.0)

        finally:
            # Cerramos la ventana y terminamos la grabación correctamente.
            app.destroy()
            ffmpeg.communicate(input=b'q\n', timeout=10)
            print('Video:', video, video.stat().st_size, 'bytes')

finally:
    xvfb.terminate()
    xvfb.wait(timeout=5)
