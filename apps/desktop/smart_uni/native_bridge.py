"""Puente ctypes explícito Python -> Rust; no modifica UI ni login.

Se carga solo con ruta local suministrada; no hay descarga de binarios,
token remoto ni fallback silencioso si Rust falla.
"""

from __future__ import annotations

import ctypes
import json
import os
from pathlib import Path


class NativeCoreError(RuntimeError):
    """La biblioteca no existe o rechazó un mensaje del contrato."""


class NativeCore:
    ABI_VERSION = 1

    def __init__(self, path: str | os.PathLike[str] | None = None):
        location = path or os.environ.get("SMARTUNI_NATIVE_LIB")
        if not location:
            raise NativeCoreError("Indica la ruta de la biblioteca local SMARTUNI_NATIVE_LIB.")
        resolved = Path(location).expanduser().resolve(strict=True)
        self._native = ctypes.CDLL(str(resolved))
        self._native.smartuni_abi_version.argtypes = []
        self._native.smartuni_abi_version.restype = ctypes.c_uint32
        if self._native.smartuni_abi_version() != self.ABI_VERSION:
            raise NativeCoreError("Versión de ABI incompatible.")
        for name in ("smartuni_validate_email_v1", "smartuni_validate_operation_v1"):
            fn = getattr(self._native, name)
            fn.argtypes = (ctypes.c_void_p, ctypes.c_size_t)
            fn.restype = ctypes.c_int32

    def _invoke(self, name: str, payload: bytes) -> None:
        if not payload:
            raise NativeCoreError("Entrada vacía.")
        buffer = ctypes.create_string_buffer(payload)
        result = getattr(self._native, name)(ctypes.cast(buffer, ctypes.c_void_p), len(payload))
        if result != 0:
            raise NativeCoreError(f"Rust rechazó la entrada (estado {result}).")

    def validate_email(self, email: str) -> None:
        self._invoke("smartuni_validate_email_v1", email.encode("utf-8"))

    def validate_operation(self, operation: dict) -> None:
        document = json.dumps(operation, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
        self._invoke("smartuni_validate_operation_v1", document)
