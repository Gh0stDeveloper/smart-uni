"""Pruebas de límites de capas y compatibilidad de SMART UNI, etapa 2.1."""

import json
import tempfile
import unittest
from pathlib import Path

from smart_uni.core import SmartUniService, ValidationError, validate_email, verify_password
from smart_uni.domain import ValidationError as DomainValidationError
from smart_uni.repository import JsonRepository, RecordRepository
from smart_uni.session import SessionState
from smart_uni.student_data import StudentSpaceService, SUBJECTS


class MemoryRepository:
    def __init__(self, path):
        self.path = path
        self.state = {
            "version": 1, "students": [], "courses": [], "announcements": [],
        }

    def read(self):
        return json.loads(json.dumps(self.state))

    def write(self, data):
        self.state = json.loads(json.dumps(data))


class TestLayerBoundaries(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / "data.json"

    def test_existing_domain_imports_remain_compatible(self):
        self.assertIs(ValidationError, DomainValidationError)
        self.assertEqual(validate_email("ESTUDIANTE@UNI.EDU"), "estudiante@uni.edu")

    def test_repository_reads_existing_version_one(self):
        original = {
            "version": 1, "students": [], "courses": [], "announcements": [],
            "student_spaces": {"legacy@uni.edu": {"tasks": []}},
        }
        self.path.write_text(json.dumps(original), encoding="utf-8")
        service = SmartUniService(self.path)
        self.assertEqual(service._read(), original)
        self.assertEqual(self.path.read_text(encoding="utf-8"), json.dumps(original))
        self.assertIsInstance(service.repository, JsonRepository)

    def test_service_accepts_repository_port_and_keeps_business_logic(self):
        fake = MemoryRepository(self.path)
        service = SmartUniService(self.path, repository=fake)
        account = service.register("Usuario Sintético", "usuario@uni.edu", "Ciencias", "ClaveSoloPrueba123")
        self.assertEqual(account["email"], "usuario@uni.edu")
        self.assertIsNotNone(service.authenticate(account["email"], "ClaveSoloPrueba123"))
        self.assertTrue(verify_password("ClaveSoloPrueba123", fake.state["students"][0]["password_hash"]))
        self.assertEqual(service.summary()["total_courses"], 0)
        self.assertTrue(isinstance(fake, RecordRepository))

    def test_student_data_still_uses_service_without_ui(self):
        service = SmartUniService(self.path)
        service.register("Usuario Sintético", "usuario@uni.edu", "Ciencias", "ClaveSoloPrueba123")
        student = StudentSpaceService(service)
        item = student.add_task("usuario@uni.edu", "Actividad", SUBJECTS[0], "2026-11-20")
        self.assertEqual(item["title"], student.overview("usuario@uni.edu")["tasks"][0]["title"])

    def test_session_is_ephemeral_and_protects_internal_mapping(self):
        session = SessionState()
        self.assertIsNone(session.user)
        identity = {"name": "Ejemplo", "email": "ejemplo@uni.edu", "career": "Ingeniería"}
        session.set_user(identity)
        identity["name"] = "Cambio externo"
        self.assertEqual(session.user["name"], "Ejemplo")
        copy_of_user = session.user
        copy_of_user["name"] = "Cambio posterior"
        self.assertEqual(session.user["name"], "Ejemplo")
        session.logout()
        self.assertIsNone(session.user)

    def test_session_rejects_incomplete_identity(self):
        session = SessionState()
        with self.assertRaises(ValueError):
            session.set_user({"name": "Incompleta"})
        self.assertIsNone(session.user)


if __name__ == "__main__":
    unittest.main()
