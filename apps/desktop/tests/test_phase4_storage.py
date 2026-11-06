"""Pruebas SQLCipher reales Windows y Linux con secretos sintéticos."""
import json
import os
import tempfile
import unittest
from pathlib import Path

try:
    from sqlcipher3 import dbapi2 as sqlcipher
    HAS_CIPHER = True
except ImportError:
    HAS_CIPHER = False

from smart_uni.secure_storage import (
    EncryptedSQLiteRepository, KeyUnavailable, StorageError, OSKeyStore,
)

INITIAL = {"version": 1, "students": [], "courses": [], "announcements": []}


class MemoryKeys:
    def __init__(self):
        self.keys = {}

    def get(self, identifier):
        return self.keys.get(identifier)

    def put(self, identifier, key):
        self.keys[identifier] = key


@unittest.skipUnless(HAS_CIPHER, "Instalar SQLCipher para ejecutar tests de 4.1")
class TestEncryptedSQLite(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / "private.sqlite"
        self.keys = MemoryKeys()

    def repo(self):
        return EncryptedSQLiteRepository(self.path, INITIAL, key_store=self.keys)

    def test_sqlcipher_encryption_and_reopen(self):
        repo = self.repo()
        data = repo.read()
        data["students"].append({
            "email": "sintetico@uni.edu", "name": "Nombre sintético",
            "career": "Ciencias", "password_hash": "hash-de-prueba",
        })
        repo.write(data)
        repo.integrity_check()
        self.assertEqual(self.repo().read(), data)
        raw = self.path.read_bytes()
        self.assertNotEqual(raw[:16], b"SQLite format 3\x00")
        self.assertNotIn(b"sintetico@uni.edu", raw)
        self.assertNotIn(b"Nombre sint", raw)

    def test_wrong_and_missing_key_never_reinitialize(self):
        self.repo()
        before = self.path.read_bytes()
        with self.assertRaises(KeyUnavailable):
            EncryptedSQLiteRepository(self.path, INITIAL, key_store=MemoryKeys())
        wrong = MemoryKeys()
        wrong.put(next(iter(self.keys.keys)), os.urandom(32))
        with self.assertRaises(StorageError):
            EncryptedSQLiteRepository(self.path, INITIAL, key_store=wrong)
        self.assertEqual(self.path.read_bytes(), before)

    def test_invalid_input_does_not_overwrite(self):
        repo = self.repo()
        with self.assertRaises(StorageError):
            repo.write({"version": 2, "students": [], "courses": [], "announcements": []})
        self.assertEqual(repo.read(), INITIAL)

    def test_plaintext_sqlite_refused_without_fallback(self):
        with sqlcipher.connect(str(self.path)) as con:
            con.execute("CREATE TABLE dummy (x TEXT)")
            con.execute("INSERT INTO dummy VALUES ('plaintext')")
        with self.assertRaises(StorageError):
            self.repo()
        self.assertTrue(self.path.exists())

    def test_secure_backend_allowlist_is_not_any_keyring(self):
        self.assertFalse(type("Plaintext", (), {}).__module__.startswith(OSKeyStore._SAFE))


if __name__ == "__main__":
    unittest.main()
