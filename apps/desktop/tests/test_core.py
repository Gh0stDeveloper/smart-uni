"""Aquí comprobamos con assert que las funciones de SMART UNI sí funcionan.

Podemos ejecutar estas cinco pruebas desde Visual Studio Code con:
python -m unittest discover -s tests -v
"""

import json
import tempfile
import unittest
from pathlib import Path

from smart_uni.core import (
    SmartUniService,
    ValidationError,
    seed_demo,
    verify_password,
)


class TestSmartUni(unittest.TestCase):
    def setUp(self):
        """Cada prueba empieza con su propio archivo JSON temporal."""
        self.folder = tempfile.TemporaryDirectory()
        self.db_file = Path(self.folder.name) / 'smart_uni.json'
        self.db = SmartUniService(self.db_file)

    def tearDown(self):
        """Al terminar borramos los datos que solo usamos para la prueba."""
        self.folder.cleanup()

    def test_01_registration_and_login(self):
        # Primero registramos una cuenta y comprobamos que podamos entrar.
        account = self.db.register(
            'María Pérez',
            'maria@universidad.edu',
            'Ingeniería',
            'ClaveSegura123',
        )

        assert account['email'] == 'maria@universidad.edu'

        assert self.db.authenticate(
            'MARIA@UNIVERSIDAD.EDU',
            'ClaveSegura123',
        )['name'] == 'María Pérez'

        # Con una contraseña incorrecta no debe iniciar sesión.
        assert self.db.authenticate(
            'maria@universidad.edu',
            'incorrecta',
        ) is None

    def test_02_duplicate_email_is_rejected(self):
        # No permitimos que dos alumnos usen el mismo correo.
        self.db.register(
            'María Pérez',
            'maria@uni.edu',
            'Ingeniería',
            'ClaveSegura123',
        )

        with self.assertRaisesRegex(ValidationError, 'ya está registrado'):
            self.db.register(
                'Otra Persona',
                'MARIA@UNI.EDU',
                'Diseño',
                'ClaveSegura123',
            )

    def test_03_json_persistence_and_no_plain_password(self):
        # Aquí verificamos que la información permanezca guardada en JSON.
        self.db.register(
            'Carlos López',
            'carlos@uni.edu',
            'Informática',
            'ClaveSegura123',
        )

        saved = json.loads(self.db_file.read_text(encoding='utf-8'))

        assert len(saved['students']) == 1
        assert saved['students'][0]['password_hash'].startswith('pbkdf2_sha256$')
        assert 'ClaveSegura123' not in self.db_file.read_text(encoding='utf-8')
        assert verify_password(
            'ClaveSegura123',
            saved['students'][0]['password_hash'],
        )

        # Volvemos a abrir el mismo archivo, como si reiniciáramos el sistema.
        reopened = SmartUniService(self.db_file)
        assert reopened.authenticate('carlos@uni.edu', 'ClaveSegura123') is not None

    def test_04_courses_schedule_and_search(self):
        # Revisamos el número de cursos, la búsqueda y el orden del horario.
        assert len(self.db.courses()) == 4
        assert len(self.db.courses('bases de datos')) == 1
        assert self.db.schedule()[0]['dia'] == 'Lunes'
        assert self.db.summary()['average_progress'] == 69

    def test_05_invalid_data_and_demo(self):
        # Primero intentamos registrar datos inválidos.
        with self.assertRaises(ValidationError):
            self.db.register('A', 'correo-invalido', 'X', '123')

        # La cuenta de demostración se puede preparar varias veces sin duplicarse.
        seed_demo(self.db)
        seed_demo(self.db)

        assert self.db.authenticate('demo@smartuni.edu', 'Demo1234!') is not None
        assert len(
            json.loads(self.db_file.read_text(encoding='utf-8'))['students']
        ) == 1


if __name__ == '__main__':
    unittest.main()
