"""Deterministic native ABI mutation testing, Rust library REQUIRED.

This is bounded fuzz-like mutation/regression testing, not coverage-guided
libFuzzer or an independent C++/JNI memory-safety audit.
"""
from __future__ import annotations

import ctypes
import os
import random
import sys


def run():
    path = os.environ.get("SMARTUNI_NATIVE_LIB")
    if not path or not os.path.isfile(path):
        raise RuntimeError("SMARTUNI_NATIVE_LIB obligatorio; no omitir test nativo")
    lib = ctypes.CDLL(path)
    buffer_type = ctypes.c_void_p
    fn_args = [buffer_type, ctypes.c_size_t, buffer_type, ctypes.c_size_t,
               buffer_type, ctypes.c_size_t, buffer_type, ctypes.c_size_t,
               ctypes.POINTER(ctypes.c_size_t)]
    lib.smartuni_seal_record_v1.argtypes = fn_args
    lib.smartuni_open_record_v1.argtypes = fn_args
    lib.smartuni_seal_record_v1.restype = ctypes.c_int32
    lib.smartuni_open_record_v1.restype = ctypes.c_int32

    key = ctypes.create_string_buffer(bytes(range(32)), 32)
    context = b"phase9/fuzz/mutation"
    ctx = ctypes.create_string_buffer(context, len(context))
    plain = b"synthetic-only-native-regression"
    data = ctypes.create_string_buffer(plain, len(plain))
    encrypted = ctypes.create_string_buffer(512)
    written = ctypes.c_size_t()
    code = lib.smartuni_seal_record_v1(
        key, 32, ctx, len(context), data, len(plain),
        encrypted, 512, ctypes.byref(written))
    if code != 0 or written.value < 40:
        raise AssertionError("No se pudo preparar el contenedor de control real")
    good = encrypted.raw[:written.value]
    output = ctypes.create_string_buffer(512)
    good_buf = ctypes.create_string_buffer(good, len(good))
    length = ctypes.c_size_t(0)
    ok = lib.smartuni_open_record_v1(
        key, 32, ctx, len(context), good_buf, len(good),
        output, len(output), ctypes.byref(length))
    if ok != 0 or output.raw[:length.value] != plain:
        raise AssertionError("Fallo de control criptográfico sano")
    rng = random.Random(0x534D415254)
    for i in range(640):
        if i < len(good):
            candidate = bytearray(good)
            candidate[i] ^= 0x01
        elif i % 3 == 0:
            candidate = bytearray(good[:rng.randrange(len(good))])
        else:
            candidate = bytearray(rng.randbytes(rng.randrange(1, 256)))
        buf = ctypes.create_string_buffer(bytes(candidate), max(1, len(candidate)))
        untouched = ctypes.create_string_buffer(b"\xa5" * 512, 512)
        count = ctypes.c_size_t(999999)
        status = lib.smartuni_open_record_v1(
            key, 32, ctx, len(context), buf, len(candidate),
            untouched, len(untouched), ctypes.byref(count))
        if status == 0 or count.value != 0 or untouched.raw != b"\xa5" * 512:
            raise AssertionError(f"La mutación {i} atravesó la autenticación o alteró salida")
    print("PASS: 640 mutaciones reproducibles del contenedor + 1 roundtrip ABI real")


if __name__ == "__main__":
    try:
        run()
    except (AssertionError, RuntimeError) as exc:
        print("FAIL:", exc, file=sys.stderr)
        sys.exit(1)
