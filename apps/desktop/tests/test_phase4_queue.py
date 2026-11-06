"""Prueba atómica snapshot+outbox real en SQLCipher sin red."""
import tempfile
import unittest
import uuid
from pathlib import Path

try:
    import sqlcipher3
    HAS_CIPHER = True
except ImportError:
    HAS_CIPHER = False

from smart_uni.offline_queue import OfflineOutbox, make_message
from smart_uni.secure_storage import EncryptedSQLiteRepository, StorageError
from test_phase4_storage import MemoryKeys, INITIAL


@unittest.skipUnless(HAS_CIPHER, "Se necesita SQLCipher para probar cola offline")
class TestOfflineQueue(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.path = Path(self.tmp.name) / "outbox.sqlcipher"
        self.keys = MemoryKeys()
        self.repo = EncryptedSQLiteRepository(self.path, INITIAL, key_store=self.keys)
        self.queue = OfflineOutbox(self.repo)

    def message(self, op_id=None):
        return make_message("notes.create", "alumno@uni.edu", {"title": "Sintético"},
                            operation_id=op_id)

    @staticmethod
    def mutate(doc):
        doc["announcements"].append({"fecha": "11 nov", "titulo": "sintético", "detalle": "local"})
        return len(doc["announcements"])

    def test_atomic_snapshot_and_queue_persist(self):
        msg = self.message()
        written, result = self.queue.apply(msg, self.mutate)
        self.assertTrue(written)
        self.assertEqual(result, 1)
        self.assertEqual(len(self.repo.read()["announcements"]), 1)
        self.assertEqual(self.queue.status()["label"], "Pendiente")
        reopened = OfflineOutbox(EncryptedSQLiteRepository(self.path, INITIAL, key_store=self.keys))
        self.assertEqual(reopened.pending()[0]["operation"]["operation_id"], msg["operation_id"])
        self.assertEqual(reopened.status()["pending"], 1)

    def test_duplicate_operation_never_replays_change(self):
        msg = self.message()
        self.queue.apply(msg, self.mutate)
        self.assertEqual(self.queue.apply(msg, self.mutate), (False, None))
        self.assertEqual(len(self.repo.read()["announcements"]), 1)
        self.assertEqual(len(self.queue.pending()), 1)

    def test_rollback_if_domain_mutation_fails(self):
        before = self.repo.read()
        with self.assertRaisesRegex(RuntimeError, "simulado"):
            self.queue.apply(self.message(), lambda doc: (_ for _ in ()).throw(RuntimeError("simulado")))
        self.assertEqual(self.repo.read(), before)
        self.assertEqual(self.queue.pending(), [])

    def test_rollback_after_outbox_insert_simulates_crash(self):
        before = self.repo.read()
        def crash(step):
            if step == "after_outbox":
                raise RuntimeError("interrupción")
        with self.assertRaises(RuntimeError):
            self.queue.apply(self.message(), self.mutate, failpoint=crash)
        self.assertEqual(self.repo.read(), before)
        self.assertEqual(self.queue.pending(), [])

    def test_error_retry_without_claiming_remote_sync(self):
        msg = self.message()
        self.queue.apply(msg, self.mutate)
        self.assertTrue(self.queue.mark_failed(msg["operation_id"]))
        self.assertEqual(self.queue.status()["label"], "Error")
        self.assertEqual(self.queue.status()["errors"], 1)
        self.assertTrue(self.queue.retry(msg["operation_id"]))
        self.assertEqual(self.queue.status()["label"], "Pendiente")
        self.assertFalse(self.queue.status()["remote_confirmed"])
        self.assertEqual(self.queue.pending()[0]["attempts"], 1)

    def test_invalid_contract_and_no_plaintext_material(self):
        msg = self.message()
        msg["schema_version"] = "9.0.0"
        with self.assertRaises(StorageError):
            self.queue.apply(msg, self.mutate)
        self.assertEqual(self.queue.status()["label"], "Sin conexión")
        self.assertFalse(self.queue.status()["remote_confirmed"])
        self.assertNotIn(b"alumno@uni.edu", self.path.read_bytes())


if __name__ == "__main__":
    unittest.main()
