"""Integración segura opt-in: migración, UI legado y outbox offline."""
import tempfile
import unittest
from pathlib import Path

try:
    import sqlcipher3
    HAS_CIPHER = True
except ImportError:
    HAS_CIPHER = False

from smart_uni.core import seed_demo
from smart_uni.offline_queue import OfflineOutbox
from smart_uni.secure_storage import KeyUnavailable, StorageError
from smart_uni.storage_mode import open_service
from smart_uni.student_data import StudentSpaceService, SUBJECTS
from test_phase4_storage import MemoryKeys


@unittest.skipUnless(HAS_CIPHER, "SQLCipher requerido en CI segura")
class TestSecureMode(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.addCleanup(self.folder.cleanup)
        self.root = Path(self.folder.name)
        self.legacy = self.root / "data.json"
        self.keys = MemoryKeys()

    def secure(self):
        return open_service(self.legacy, mode="secure", key_store=self.keys)

    def test_secure_initialization_does_not_seed_public_demo(self):
        service = self.secure()
        self.assertEqual(service._read()["students"], [])
        self.assertFalse(self.legacy.exists())
        self.assertTrue(self.root.joinpath("data.sqlcipher").exists())
        self.assertEqual(OfflineOutbox(service.repository).status()["label"], "Sin conexión")

    def test_legacy_mode_unchanged_and_explicit_migration(self):
        legacy_service = open_service(self.legacy, mode="legacy")
        seed_demo(legacy_service)
        before = self.legacy.read_bytes()
        service = self.secure()
        self.assertIsNotNone(service.authenticate("demo@smartuni.edu", "Demo1234!"))
        self.assertEqual(self.legacy.read_bytes(), before)
        self.assertEqual(self.secure()._read(), service._read())
        self.assertNotIn(b"demo@smartuni.edu", self.root.joinpath("data.sqlcipher").read_bytes())

    def test_students_use_encrypted_store_with_atomic_outbox(self):
        service = self.secure()
        service.register("Estudiante Seguro", "estudiante@uni.edu", "Ciencias", "ClaveSegura123")
        student = StudentSpaceService(service)
        note = student.add_note("estudiante@uni.edu", "Título", SUBJECTS[0], "Texto privado")
        student.update_note("estudiante@uni.edu", note["id"], "Título 2", "Texto actualizado")
        task = student.add_task("estudiante@uni.edu", "Entregar", SUBJECTS[0], "2026-11-25")
        student.toggle_task("estudiante@uni.edu", task["id"])
        student.remove("estudiante@uni.edu", "notes", note["id"])
        student.update_profile("estudiante@uni.edu", "Nombre Actualizado", "Ingeniería")
        pending = OfflineOutbox(service.repository).pending()
        self.assertEqual(len(pending), 6)
        self.assertEqual([p["operation"]["operation"] for p in pending], [
            "notes.create", "notes.update", "tasks.create",
            "tasks.toggle", "notes.delete", "profile.update",
        ])
        self.assertEqual(OfflineOutbox(service.repository).status()["label"], "Pendiente")
        self.assertEqual(self.secure().authenticate("estudiante@uni.edu", "ClaveSegura123")["name"],
                         "Nombre Actualizado")
        self.assertNotIn(b"Texto actualizado", service.path.read_bytes())

    def test_materials_refused_without_encrypted_attachments(self):
        service = self.secure()
        service.register("Estudiante Seguro", "estudiante@uni.edu", "Ciencias", "ClaveSegura123")
        path = self.root / "informe.md"
        path.write_text("Contenido sintético", encoding="utf-8")
        with self.assertRaisesRegex(Exception, "pendiente"):
            StudentSpaceService(service).add_material("estudiante@uni.edu", SUBJECTS[0], str(path))
        self.assertFalse(self.root.joinpath("materiales").exists())

    def test_missing_keystore_fails_closed_after_creation(self):
        self.secure()
        original = self.root.joinpath("data.sqlcipher").read_bytes()
        with self.assertRaises(KeyUnavailable):
            open_service(self.legacy, mode="secure", key_store=MemoryKeys())
        self.assertEqual(self.root.joinpath("data.sqlcipher").read_bytes(), original)

    def test_unknown_storage_mode_rejected(self):
        with self.assertRaises(StorageError):
            open_service(self.legacy, mode="plaintext-unsafe", key_store=self.keys)


if __name__ == "__main__":
    unittest.main()
