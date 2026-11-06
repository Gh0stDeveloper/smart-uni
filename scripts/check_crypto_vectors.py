#!/usr/bin/env python3
"""Verifica vectores AES-256-GCM con cryptography/OpenSSL, independiente de Rust."""

import json
from pathlib import Path

from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "core/rust/test-vectors/aes256gcm.json"


def verify() -> None:
    vectors = json.loads(SOURCE.read_text(encoding="utf-8"))
    assert vectors["algorithm"] == "AES-256-GCM"
    assert len(vectors["vectors"]) >= 2
    for item in vectors["vectors"]:
        key = bytes.fromhex(item["key_hex"])
        nonce = bytes.fromhex(item["nonce_hex"])
        aad = bytes.fromhex(item["aad_hex"])
        plaintext = bytes.fromhex(item["plaintext_hex"])
        expected = bytes.fromhex(item["ciphertext_hex"] + item["tag_hex"])
        assert len(key) == 32 and len(nonce) == 12 and len(item["tag_hex"]) == 32
        impl = AESGCM(key)
        assert impl.encrypt(nonce, plaintext, aad) == expected, item["id"]
        assert impl.decrypt(nonce, expected, aad) == plaintext, item["id"]
        corrupted = bytearray(expected)
        corrupted[-1] ^= 1
        try:
            impl.decrypt(nonce, bytes(corrupted), aad)
        except InvalidTag:
            pass
        else:
            raise AssertionError("Debe rechazarse etiqueta alterada: " + item["id"])
        print("AES-256-GCM OpenSSL: OK", item["id"])
    print("Vectores independientes aprobados:", len(vectors["vectors"]))


if __name__ == "__main__":
    verify()
