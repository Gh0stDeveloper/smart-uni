"""Recuperación de clave SQLCipher con Rust Argon2id, pruebas aisladas."""
import os
import tempfile
import unittest
from pathlib import Path

try:
    from sqlcipher3 import dbapi2
    CIPHER = True
except ImportError:
    CIPHER = False

from smart_uni.secure_storage import EncryptedSQLiteRepository, KeyUnavailable, StorageError
from smart_uni.key_recovery import export_database_recovery, restore_database_recovery
from test_phase4_storage import MemoryKeys, INITIAL


@unittest.skipUnless(CIPHER and os.environ.get("SMARTUNI_NATIVE_LIB"),
                     "Requiere SQLCipher y Rust real")
class TestDatabaseRecovery(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / "encrypted.sqlcipher"
        self.keys = MemoryKeys()
        self.repo = EncryptedSQLiteRepository(self.path, INITIAL, key_store=self.keys)
        self.phrase = "recuperacion ficticia " + os.urandom(24).hex()

    def test_lost_database_key_recovered_without_plaintext(self):
        actual = self.repo.read()
        package = export_database_recovery(self.repo, self.phrase)
        self.assertEqual(package[:8], b"SURECV01")
        self.keys.keys.clear()
        with self.assertRaises(KeyUnavailable):
            EncryptedSQLiteRepository(self.path, INITIAL, key_store=self.keys)
        with self.assertRaises(Exception):
            restore_database_recovery(self.path, package, self.phrase + "BAD", key_store=self.keys)
        self.assertEqual(self.keys.keys, {})
        restore_database_recovery(self.path, package, self.phrase, key_store=self.keys)
        reloaded = EncryptedSQLiteRepository(self.path, INITIAL, key_store=self.keys)
        self.assertEqual(reloaded.read(), actual)
        self.assertNotIn(b"students", self.path.read_bytes())

    def test_corrupt_package_and_wrong_database_refused(self):
        package = export_database_recovery(self.repo, self.phrase)
        backup = bytearray(package); backup[-1] ^= 1
        empty = MemoryKeys()
        with self.assertRaises(Exception):
            restore_database_recovery(self.path, bytes(backup), self.phrase, key_store=empty)
        self.assertFalse(empty.keys)
        second = Path(self.temp.name) / "other.sqlcipher"
        EncryptedSQLiteRepository(second, INITIAL, key_store=MemoryKeys())
        with self.assertRaises(StorageError):
            restore_database_recovery(second, package, self.phrase, key_store=empty)
        self.assertFalse(empty.keys)


if __name__ == "__main__":
    unittest.main()
