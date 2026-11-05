"""Pruebas de los nuevos apartados, con assert y un JSON temporal."""

import tempfile
import unittest
from datetime import date
from pathlib import Path

from smart_uni.core import SmartUniService, ValidationError, seed_demo
from smart_uni.student_data import (
    SUBJECTS,
    StudentSpaceService,
    seed_student_demo,
)


class TestStudentSpace(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.base = SmartUniService(Path(self.folder.name) / 'datos.json')
        seed_demo(self.base)
        self.base.register('Estudiante Dos', 'alumno2@uni.edu', 'Informática', 'ClaveSegura123')
        self.space = StudentSpaceService(self.base)
        self.demo = 'demo@smartuni.edu'
        self.other = 'alumno2@uni.edu'

    def tearDown(self):
        self.folder.cleanup()

    def test_01_materias_de_las_capturas(self):
        assert len(SUBJECTS) == 8
        assert 'Cálculo' in SUBJECTS
        assert 'Proyecto Integrador' in SUBJECTS
        assert 'Fundamentos de Informática' in SUBJECTS

    def test_02_usuarios_separados(self):
        self.space.add_friend(self.demo, 'Ana', 'ana@uni.edu')
        assert len(self.space.overview(self.demo)['friends']) == 1
        assert self.space.overview(self.other)['friends'] == []

    def test_03_amigos_duplicados_y_eliminacion(self):
        person = self.space.add_friend(self.demo, 'Ana', 'ana@uni.edu')
        with self.assertRaises(ValidationError):
            self.space.add_friend(self.demo, 'Otra Ana', 'ANA@UNI.EDU')
        assert self.space.remove(self.demo, 'friends', person['id'])
        assert not self.space.overview(self.demo)['friends']

    def test_04_eventos_y_validacion_de_fechas(self):
        event = self.space.add_event(self.demo, 'Examen de Cálculo', '2026-11-17', 'Examen')
        assert event['date'] == '2026-11-17'
        with self.assertRaises(ValidationError):
            self.space.add_event(self.demo, 'Evento inválido', '2026-02-31')
        assert len(self.space.overview(self.demo)['events']) == 1

    def test_05_tareas_se_guardan_y_se_marcan(self):
        task = self.space.add_task(self.demo, 'Entregar programa', 'Programa Estructurado', '2026-11-22')
        assert not task['done']
        assert self.space.toggle_task(self.demo, task['id'])
        reloaded = StudentSpaceService(SmartUniService(self.base.path))
        assert reloaded.overview(self.demo)['tasks'][0]['done']
        assert not reloaded.toggle_task(self.demo, task['id'])

    def test_06_apuntes_crear_editar_eliminar(self):
        note = self.space.add_note(self.demo, 'Resumen', 'Cálculo', 'Primera versión')
        self.space.update_note(self.demo, note['id'], 'Resumen actualizado', 'Segunda versión')
        saved = self.space.overview(self.demo)['notes'][0]
        assert saved['title'] == 'Resumen actualizado'
        assert saved['content'] == 'Segunda versión'
        assert self.space.remove(self.demo, 'notes', note['id'])

    def test_07_materiales_importar_abrir_y_eliminar(self):
        original = Path(self.folder.name) / 'apuntes.pdf'
        original.write_bytes(b'%PDF-1.4\nArchivo de prueba')
        resource = self.space.add_material(self.demo, 'Cálculo', str(original))
        saved_path = self.space.material_path(self.demo, resource['id'])
        assert saved_path.is_file()
        assert saved_path.read_bytes() == original.read_bytes()
        assert self.space.delete_material(self.demo, resource['id'])
        assert not saved_path.exists()

    def test_08_perfil_y_cuentas_anteriores(self):
        account = self.space.update_profile(self.demo, 'Nuevo Nombre', 'Diseño de Software')
        assert account['career'] == 'Diseño de Software'
        assert self.base.authenticate(self.demo, 'Demo1234!')['name'] == 'Nuevo Nombre'
        assert len(self.base.courses()) == 4

    def test_09_contenido_demostrativo_solo_en_demo(self):
        seed_student_demo(self.space)
        seed_student_demo(self.space)
        assert len(self.space.overview(self.demo)['events']) == 3
        assert len(self.space.overview(self.demo)['tasks']) == 2
        assert not any(self.space.overview(self.other).values())

    def test_10_validacion_de_material_inseguro(self):
        path = Path(self.folder.name) / 'ejecutar.exe'
        path.write_bytes(b'MZ')
        with self.assertRaises(ValidationError):
            self.space.add_material(self.demo, 'Cálculo', str(path))


if __name__ == '__main__':
    unittest.main()
