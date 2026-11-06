"""Pruebas cruzadas Rust / OpenSSL / Argon2id, Windows/Linux, datos sintéticos."""
import os
import unittest

from smart_uni.secure_crypto import ContentCrypto
from smart_uni.native_bridge import NativeCoreError

try:
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    from argon2.low_level import hash_secret_raw, Type
    AVAILABLE = True
except ImportError:
    AVAILABLE = False


@unittest.skipUnless(os.environ.get("SMARTUNI_NATIVE_LIB") and AVAILABLE,
                     "Se necesita biblioteca Rust y cryptography/argon2-cffi en CI nativa")
class TestPhase6Interop(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.native = ContentCrypto()

    def test_rust_seal_python_opens(self):
        key = os.urandom(32)
        context = b"owner/user-a/resource/test/epoch-1"
        plaintext = "Nota de prueba sin datos reales 🔐".encode("utf-8")
        container = self.native.encrypt(key, context, plaintext)
        self.assertEqual(container[:8], b"SUAEAD01")
        self.assertEqual(container[8], 1)
        length = int.from_bytes(container[9:11], "big")
        self.assertEqual(container[23:23 + length], context)
        header = container[:23 + length]
        self.assertEqual(
            AESGCM(key).decrypt(container[11:23], container[23 + length:], header),
            plaintext,
        )
        self.assertNotIn(plaintext, container)

    def test_python_seal_rust_opens(self):
        key = os.urandom(32)
        context = b"owner/user-a/resource/python/epoch-9"
        plaintext = b"mensaje de prueba " * 70
        nonce = os.urandom(12)
        header = b"SUAEAD01" + b"\x01" + len(context).to_bytes(2, "big") + nonce + context
        container = header + AESGCM(key).encrypt(nonce, plaintext, header)
        self.assertEqual(self.native.decrypt(key, context, container), plaintext)
        with self.assertRaises(NativeCoreError):
            self.native.decrypt(key, b"owner/user-b/resource/python/epoch-9", container)

    def test_wrong_key_and_modified_ciphertext_fail_closed(self):
        key = os.urandom(32)
        context = b"owner/test/file/123/epoch-1"
        data = self.native.encrypt(key, context, b"synthetic")
        with self.assertRaises(NativeCoreError):
            self.native.decrypt(os.urandom(32), context, data)
        damaged = bytearray(data)
        damaged[-1] ^= 1
        with self.assertRaises(NativeCoreError):
            self.native.decrypt(key, context, bytes(damaged))
        with self.assertRaises(NativeCoreError):
            self.native.decrypt(key, context, data[:10])

    def test_recovery_export_rust_open_python(self):
        key = os.urandom(32)
        passphrase = "Una frase aleatoria ficticia " + os.urandom(12).hex()
        package = self.native.export_recovery(key, passphrase)
        self.assertEqual(len(package), 84)
        self.assertEqual(package[:8], b"SURECV01")
        wrap = hash_secret_raw(passphrase.encode("utf-8"), package[8:24],
            time_cost=3, memory_cost=65536, parallelism=1, hash_len=32,
            type=Type.ID, version=19)
        recovered = AESGCM(wrap).decrypt(package[24:36], package[36:], package[:36])
        self.assertEqual(recovered, key)
        with self.assertRaises(NativeCoreError):
            self.native.restore_recovery(package, passphrase + "alterada")

    def test_recovery_python_export_rust_open(self):
        key = os.urandom(32)
        phrase = "frase ficticia de alta entropia " + os.urandom(16).hex()
        salt, nonce = os.urandom(16), os.urandom(12)
        wrap = hash_secret_raw(phrase.encode(), salt,
            time_cost=3, memory_cost=65536, parallelism=1, hash_len=32,
            type=Type.ID, version=19)
        header = b"SURECV01" + salt + nonce
        package = header + AESGCM(wrap).encrypt(nonce, key, header)
        self.assertEqual(self.native.restore_recovery(package, phrase), key)
        modified = bytearray(package)
        modified[-1] ^= 1
        with self.assertRaises(NativeCoreError):
            self.native.restore_recovery(bytes(modified), phrase)


if __name__ == "__main__":
    unittest.main()
