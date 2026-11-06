"""Regresión P06: límites al costo PBKDF2 del JSON heredado."""
import unittest

from smart_uni.domain import hash_password, verify_password


class PasswordCostBoundTests(unittest.TestCase):
    def test_legacy_hash_with_260000_iterations_works(self):
        stored = hash_password("ClaveDePrueba123!")
        self.assertTrue(verify_password("ClaveDePrueba123!", stored))
        self.assertFalse(verify_password("Incorrecta", stored))

    def test_malicious_iteration_count_rejected(self):
        salt = "00" * 16
        digest = "00" * 32
        for count in ("999999999999999999", "0", "1", "-1", "1000001", "١٠٠٠٠٠", "abc"):
            value = 'pbkdf2_sha256$' + count + '$' + salt + '$' + digest
            self.assertFalse(verify_password("irrelevante", value), count)

    def test_invalid_salt_digest_and_non_string(self):
        self.assertFalse(verify_password("x", "pbkdf2_sha256$260000$aa$bb"))
        self.assertFalse(verify_password("x", "pbkdf2_sha256$260000$" + "ff" * 16 + "$" + "bb" * 1000))
        self.assertFalse(verify_password("x", None))


if __name__ == "__main__":
    unittest.main()
