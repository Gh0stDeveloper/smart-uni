"""Migración, respaldo y fallos controlados sin datos reales."""
import hashlib
import json
import tempfile
import unittest
from pathlib import Path

try:
    import sqlcipher3
    CIPHER = True
except ImportError:
    CIPHER = False

from smart_uni.migration import migrate_json, create_backup, restore_backup
from smart_uni.secure_storage import StorageError, EncryptedSQLiteRepository
from test_phase4_storage import INITIAL, MemoryKeys


@unittest.skipUnless(CIPHER, "Pruebas CI con SQLCipher instalado")
class TestMigrationAndBackups(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.addCleanup(self.folder.cleanup)
        self.root = Path(self.folder.name)
        self.source = self.root / "legacy.json"
        self.target = self.root / "secure.sqlite"
        self.keys = MemoryKeys()
        self.payload = {**INITIAL, "student_spaces": {
            "alumno@uni.edu": {"notes": [{"id": "f" * 32, "content": "Privado sintético"}]}
        }}
        self.source.write_text(json.dumps(self.payload, ensure_ascii=False), encoding="utf-8")

    def migrate(self, **kwargs):
        return migrate_json(self.source, self.target, key_store=self.keys, **kwargs)

    def test_migration_retains_source_and_all_data(self):
        before = self.source.read_bytes()
        repo = self.migrate()
        self.assertEqual(repo.read(), self.payload)
        self.assertEqual(self.source.read_bytes(), before)
        self.assertNotIn(b"Privado sint", self.target.read_bytes())
        with self.assertRaises(StorageError):
            self.migrate()

    def test_interruption_before_promotion_cleans_stage_and_keeps_source(self):
        before = self.source.read_bytes()
        def interrupt(stage):
            if stage == "staged":
                raise RuntimeError("Corte simulado")
        with self.assertRaisesRegex(RuntimeError, "Corte"):
            self.migrate(on_step=interrupt)
        self.assertEqual(self.source.read_bytes(), before)
        self.assertFalse(self.target.exists())
        self.assertEqual(list(self.root.glob("*.staging")), [])
        self.assertEqual(self.migrate().read(), self.payload)

    def test_backup_and_restore_after_changes(self):
        repo = self.migrate()
        backup = self.root / "backup.sqlcipher"
        digest = create_backup(repo, backup)
        self.assertEqual(digest, hashlib.sha256(backup.read_bytes()).hexdigest())
        self.assertNotIn(b"Privado sint", backup.read_bytes())
        changed = repo.read()
        changed["announcements"].append({"fecha": "hoy", "titulo": "posterior", "detalle": "test"})
        repo.write(changed)
        previous = restore_backup(repo, backup)
        self.assertTrue(previous.exists())
        self.assertEqual(repo.read(), self.payload)
        self.assertEqual(self.source.read_text(encoding="utf-8"), json.dumps(self.payload, ensure_ascii=False))

    def test_corrupt_backup_does_not_replace_database(self):
        repo = self.migrate()
        backup = self.root / "backup.sqlcipher"
        create_backup(repo, backup)
        original = self.target.read_bytes()
        backup.write_bytes(b"truncado")
        with self.assertRaises(Exception):
            restore_backup(repo, backup)
        self.assertEqual(self.target.read_bytes(), original)

    def test_interrupted_restore_keeps_current_database(self):
        repo = self.migrate()
        backup = self.root / "backup.sqlcipher"
        create_backup(repo, backup)
        before = self.target.read_bytes()
        with self.assertRaises(RuntimeError):
            restore_backup(repo, backup, on_step=lambda stage: (_ for _ in ()).throw(RuntimeError(stage)))
        self.assertEqual(self.target.read_bytes(), before)


if __name__ == "__main__":
    unittest.main()
