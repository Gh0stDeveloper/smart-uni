"""Pruebas de biblioteca Rust REAL; omitir en escritorio sin binario compilado."""
import copy
import json
import os
import unittest
from pathlib import Path

from smart_uni.native_bridge import NativeCore, NativeCoreError

ROOT = Path(__file__).resolve().parents[3]
FIXTURE = ROOT / "packages/contracts/v1/examples/notes-create.json"


@unittest.skipUnless(os.environ.get("SMARTUNI_NATIVE_LIB"), "No se compila Rust en la suite Tkinter normal")
class TestRustFFI(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.core = NativeCore()

    def test_real_crypto_known_answer_test(self):
        self.core.crypto_self_test()

    def test_real_ffi_validates_email(self):
        self.core.validate_email("STUDENT@EXAMPLE.EDU")
        with self.assertRaises(NativeCoreError):
            self.core.validate_email("correo-invalido")

    def test_real_ffi_validates_stage_two_contract(self):
        valid = json.loads(FIXTURE.read_text(encoding="utf-8"))
        self.core.validate_operation(valid)
        future = copy.deepcopy(valid)
        future["schema_version"] = "9.0.0"
        with self.assertRaises(NativeCoreError):
            self.core.validate_operation(future)

    def test_real_ffi_rejects_invalid_actor(self):
        valid = json.loads(FIXTURE.read_text(encoding="utf-8"))
        valid["actor_ref"] = "STUDENT@EXAMPLE.EDU"
        with self.assertRaises(NativeCoreError):
            self.core.validate_operation(valid)


if __name__ == "__main__":
    unittest.main()
