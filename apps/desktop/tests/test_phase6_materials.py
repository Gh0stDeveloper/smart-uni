"""Importación cifrada sin archivo temporal plaintext; recuperación opt-in."""
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

try:
    from sqlcipher3 import dbapi2
    CIPHER = True
except ImportError:
    CIPHER = False

from smart_uni.core import SmartUniService
from smart_uni.storage_mode import open_service
from smart_uni.secure_files import SecureMaterialStore
from smart_uni.secure_crypto import ContentCrypto
from smart_uni.secure_storage import KeyUnavailable, StorageError
from smart_uni.student_data import StudentSpaceService, SUBJECTS
from smart_uni.offline_queue import OfflineOutbox
from test_phase4_storage import MemoryKeys


@unittest.skipUnless(CIPHER and os.environ.get("SMARTUNI_NATIVE_LIB"),
                     "Requiere SQLCipher y biblioteca Rust real; CI rust nativa")
class TestPhase6SecureMaterials(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.keys = MemoryKeys()
        self.service = open_service(self.root / "user.json", mode="secure", key_store=self.keys)
        self.service.register("Estudiante de prueba", "prueba@uni.edu", "Ingeniería", "ClavePrueba123!")
        self.space = StudentSpaceService(self.service)
        self.source = self.root / "origen.txt"
        self.source.write_text("Contenido sintético privado de fase 6 con ñ", encoding="utf-8")
        self.store = SecureMaterialStore(self.service.repository, "prueba@uni.edu")
        self.encrypted_dir = self.root / "encrypted-materials"

    def test_create_read_reopen_and_delete_material_with_outbox(self):
        item = self.space.add_material("prueba@uni.edu", SUBJECTS[0], str(self.source))
        self.assertEqual(item["storage"], "suaead1")
        output = self.encrypted_dir / (item["id"] + ".sun1")
        self.assertTrue(output.exists())
        self.assertEqual(output.read_bytes()[:8], b"SUAEAD01")
        self.assertNotIn(b"Contenido sint", output.read_bytes())
        self.assertNotIn(b"Contenido sint", self.service.path.read_bytes())
        self.assertEqual(
            self.space.material_bytes("prueba@uni.edu", item["id"]), self.source.read_bytes()
        )
        self.assertEqual(
            [x["operation"]["operation"] for x in OfflineOutbox(self.service.repository).pending()],
            ["materials.import"],
        )
        self.assertTrue(self.space.delete_material("prueba@uni.edu", item["id"]))
        self.assertFalse(output.exists())
        self.assertEqual(
            [x["operation"]["operation"] for x in OfflineOutbox(self.service.repository).pending()],
            ["materials.import", "materials.delete"],
        )

    def test_wrong_owner_tamper_and_plaintext_path_refused(self):
        item = self.space.add_material("prueba@uni.edu", SUBJECTS[0], str(self.source))
        with self.assertRaisesRegex(Exception, "bloqueado"):
            self.space.material_path("prueba@uni.edu", item["id"])
        output = self.encrypted_dir / (item["id"] + ".sun1")
        tampered = bytearray(output.read_bytes())
        tampered[-1] ^= 0x01
        output.write_bytes(tampered)
        with self.assertRaises(Exception):
            self.space.material_bytes("prueba@uni.edu", item["id"])
        with self.assertRaises(Exception):
            self.space.material_bytes("intruso@uni.edu", item["id"])

    def test_recovery_kept_outside_database_and_missing_key_fail_closed(self):
        item = self.space.add_material("prueba@uni.edu", SUBJECTS[0], str(self.source))
        phrase = "frase ficticia impredecible " + os.urandom(16).hex()
        package = self.store.export_recovery(phrase)
        self.assertEqual(package[:8], b"SURECV01")
        self.assertNotIn(self.store._key, package)
        self.keys.keys.pop(self.store._identifier)
        with self.assertRaises(KeyUnavailable):
            self.space.material_bytes("prueba@uni.edu", item["id"])
        with self.assertRaises(Exception):
            SecureMaterialStore.restore_content_key(
                self.service.repository, "prueba@uni.edu", package, phrase + "incorrecta"
            )
        SecureMaterialStore.restore_content_key(
            self.service.repository, "prueba@uni.edu", package, phrase
        )
        self.assertEqual(
            self.space.material_bytes("prueba@uni.edu", item["id"]), self.source.read_bytes()
        )

    def test_rollback_removes_ciphertext_if_db_transaction_fails(self):
        with patch("smart_uni.secure_files.OfflineOutbox.apply", side_effect=RuntimeError("fallo simulado")):
            with self.assertRaisesRegex(RuntimeError, "fallo simulado"):
                self.space.add_material("prueba@uni.edu", SUBJECTS[0], str(self.source))
        self.assertEqual(list(self.encrypted_dir.glob("*.sun1")), [])
        self.assertEqual(OfflineOutbox(self.service.repository).pending(), [])


if __name__ == "__main__":
    unittest.main()
