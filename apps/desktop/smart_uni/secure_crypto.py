"""Puente de cifrado nativo Rust, obligatorio en modo seguro de materiales.

No crea secretos ni hace fallback a una implementación ad-hoc en Python.
Nunca imprimir claves o frases de recuperación.
"""
from __future__ import annotations

import ctypes
import os
from .native_bridge import NativeCore, NativeCoreError


class ContentCrypto:
    MAX_PLAINTEXT = 8 * 1024 * 1024

    def __init__(self, lib=None):
        self.core = lib if lib is not None else NativeCore()
        self.lib = self.core._native
        for name in ("smartuni_seal_record_v1", "smartuni_open_record_v1"):
            fn = getattr(self.lib, name)
            fn.argtypes = [ctypes.c_void_p, ctypes.c_size_t] * 3 + [
                ctypes.c_void_p, ctypes.c_size_t, ctypes.POINTER(ctypes.c_size_t),
            ]
            fn.restype = ctypes.c_int32
        for name in ("smartuni_export_recovery_v1", "smartuni_restore_recovery_v1"):
            fn = getattr(self.lib, name)
            fn.argtypes = [ctypes.c_void_p, ctypes.c_size_t] * 2 + [
                ctypes.c_void_p, ctypes.c_size_t, ctypes.POINTER(ctypes.c_size_t),
            ]
            fn.restype = ctypes.c_int32
        self.core.crypto_self_test()

    def _call(self, function: str, parts: tuple[bytes, ...], capacity: int) -> bytes:
        if capacity <= 0 or capacity > self.MAX_PLAINTEXT + 512:
            raise NativeCoreError("Capacidad de buffer inválida")
        buffers = [ctypes.create_string_buffer(part) for part in parts]
        args = []
        for buffer, part in zip(buffers, parts):
            args.extend((ctypes.cast(buffer, ctypes.c_void_p), len(part)))
        output = ctypes.create_string_buffer(capacity)
        written = ctypes.c_size_t(0)
        code = getattr(self.lib, function)(
            *args, ctypes.cast(output, ctypes.c_void_p), capacity,
            ctypes.byref(written),
        )
        if code != 0 or written.value > capacity:
            raise NativeCoreError("Operación criptográfica rechazada por Rust")
        return bytes(output.raw[:written.value])

    def encrypt(self, key: bytes, context: bytes, plaintext: bytes) -> bytes:
        if len(key) != 32 or not 1 <= len(context) <= 256 or len(plaintext) > self.MAX_PLAINTEXT:
            raise NativeCoreError("Clave, contexto o longitud inválida")
        return self._call("smartuni_seal_record_v1", (key, context, plaintext),
                          len(plaintext) + len(context) + 80)

    def decrypt(self, key: bytes, context: bytes, ciphertext: bytes) -> bytes:
        if len(key) != 32 or not 1 <= len(context) <= 256 or len(ciphertext) > self.MAX_PLAINTEXT + 300:
            raise NativeCoreError("Clave, contexto o longitud inválida")
        return self._call("smartuni_open_record_v1", (key, context, ciphertext),
                          max(len(ciphertext), 1))

    def export_recovery(self, key: bytes, phrase: str) -> bytes:
        if len(key) != 32:
            raise NativeCoreError("Clave inválida")
        encoded = phrase.encode("utf-8")
        if not 16 <= len(encoded) <= 512:
            raise NativeCoreError("Usa frase aleatoria de recuperación de alta entropía")
        return self._call("smartuni_export_recovery_v1", (key, encoded), 84)

    def restore_recovery(self, package: bytes, phrase: str) -> bytes:
        return self._call("smartuni_restore_recovery_v1",
                          (package, phrase.encode("utf-8")), 32)
