"""Aquí comprobamos que el menú nuevo reúna todas las pantallas.

Estas pruebas solo se ejecutan cuando hay pantalla gráfica disponible.
"""

import os
import sys
import tempfile
import unittest
import tkinter as tk
from pathlib import Path

from smart_uni.core import SmartUniService, seed_demo
from smart_uni.ui import SmartUniApp


@unittest.skipUnless(os.environ.get('DISPLAY') or sys.platform == 'win32',
                     'Las pruebas gráficas necesitan una pantalla')
class TestSharedNavigation(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        service = SmartUniService(Path(self.folder.name) / 'data.json')
        seed_demo(service)
        try:
            self.app = SmartUniApp(service)
        except tk.TclError:
            self.folder.cleanup()
            self.skipTest('No hay una pantalla gráfica disponible')
        self.app.withdraw()
        self.app.user = service.authenticate('demo@smartuni.edu', 'Demo1234!')

    def tearDown(self):
        self.app.destroy()
        self.folder.cleanup()

    def test_menu_unico_ubicado_arriba(self):
        self.app.show_dashboard()
        assert not self.app._nav_open
        assert self.app._hamburger.cget('text') == '☰'
        self.app._toggle_navigation()
        assert self.app._nav_open
        assert self.app._hamburger.cget('text') == '✕'
        self.app._toggle_navigation()
        assert not self.app._nav_open

    def test_todas_las_secciones_conservadas(self):
        for section in ('Inicio', 'Perfil', 'Amigos', 'Calendario',
                        'Material', 'Tareas', 'Apuntes'):
            self.app.show_student_space(section)
            assert self.app._content_holder.winfo_exists()
            assert not self.app._nav_open
        for screen in (self.app.show_courses, self.app.show_schedule,
                       self.app.show_announcements, self.app.show_dashboard):
            screen()
            assert self.app._content_holder.winfo_exists()
