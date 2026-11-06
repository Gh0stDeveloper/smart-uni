"""Offline release-manifest signature and downgrade gate.

NOT an updater. Clients MUST independently pin a trusted public key and
persist protected monotonic version state before deployment; neither exists.
"""
from __future__ import annotations

import argparse
import base64
import hashlib
import json
import re
import sys
from pathlib import Path

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

PACKAGE = "xyz.smartuni.app"
CHANNELS = {"internal", "closed", "production"}
REQUIRED = {"schema_version", "package_name", "channel", "version_code",
            "min_supported_version_code", "artifact_sha256", "artifact_size",
            "source_commit"}


class ReleaseRejected(ValueError):
    """Fail closed on invalid, untrusted or stale metadata."""


def verify_release(
    raw_manifest: bytes,
    raw_signature_b64: bytes,
    public_key_pem: bytes,
    artifact: Path,
    *,
    installed_version_code: int,
    min_allowed_version_code: int,
) -> dict:
    try:
        manifest = json.loads(raw_manifest.decode("utf-8"))
        if not isinstance(manifest, dict) or set(manifest) != REQUIRED:
            raise ReleaseRejected("Campos de manifiesto inválidos")
        if type(manifest["schema_version"]) is not int or manifest["schema_version"] != 1:
            raise ReleaseRejected("Versión de esquema no admitida")
        if manifest["package_name"] != PACKAGE or manifest["channel"] not in CHANNELS:
            raise ReleaseRejected("Paquete o canal no admitido")
        for key in ("version_code", "min_supported_version_code", "artifact_size"):
            if type(manifest[key]) is not int or manifest[key] <= 0:
                raise ReleaseRejected("Valor numérico inválido: " + key)
        version = manifest["version_code"]
        if manifest["min_supported_version_code"] > version:
            raise ReleaseRejected("Mínimo mayor que la versión")
        if type(installed_version_code) is not int or installed_version_code < 0:
            raise ReleaseRejected("Estado local inválido")
        if type(min_allowed_version_code) is not int or min_allowed_version_code < 1:
            raise ReleaseRejected("Política de versión mínima inválida")
        if version < max(installed_version_code, min_allowed_version_code):
            raise ReleaseRejected("Downgrade rechazado")
        if not isinstance(manifest["artifact_sha256"], str) or not re.fullmatch(
            r"[0-9a-f]{64}", manifest["artifact_sha256"]
        ):
            raise ReleaseRejected("Digest SHA256 inválido")
        if not isinstance(manifest["source_commit"], str) or not re.fullmatch(
            r"[0-9a-f]{40}", manifest["source_commit"]
        ):
            raise ReleaseRejected("Commit fuente no válido")

        key = serialization.load_pem_public_key(public_key_pem)
        if not isinstance(key, Ed25519PublicKey):
            raise ReleaseRejected("Solo firmas Ed25519 permitidas")
        signature = base64.b64decode(raw_signature_b64.strip(), validate=True)
        if len(signature) != 64:
            raise ReleaseRejected("Firma Ed25519 no canónica")
        # Verify EXACT bytes, not a reserialized/reordered JSON object.
        key.verify(signature, raw_manifest)

        # Bounded streaming hash; do not load APK/AAB into memory.
        sha256 = hashlib.sha256()
        total = 0
        with artifact.open("rb") as stream:
            for block in iter(lambda: stream.read(1024 * 1024), b""):
                total += len(block)
                sha256.update(block)
        if total != manifest["artifact_size"] or sha256.hexdigest() != manifest["artifact_sha256"]:
            raise ReleaseRejected("Artefacto distinto al firmado")
    except ReleaseRejected:
        raise
    except (ValueError, TypeError, OSError, InvalidSignature, KeyError) as exc:
        raise ReleaseRejected("Firma, metadatos o artefacto inválido") from exc
    return manifest


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Verificar firma/digest y política anti-downgrade")
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument("--signature-b64", required=True, type=Path)
    parser.add_argument("--public-key-pem", required=True, type=Path)
    parser.add_argument("--artifact", required=True, type=Path)
    parser.add_argument("--installed-version-code", type=int, required=True)
    parser.add_argument("--min-allowed-version-code", type=int, required=True)
    args = parser.parse_args(argv)
    try:
        manifest = verify_release(
            args.manifest.read_bytes(), args.signature_b64.read_bytes(),
            args.public_key_pem.read_bytes(), args.artifact,
            installed_version_code=args.installed_version_code,
            min_allowed_version_code=args.min_allowed_version_code,
        )
    except ReleaseRejected as exc:
        print("DENEGADO:", exc, file=sys.stderr)
        return 1
    print("APROBADO por verificador offline experimental:", manifest["version_code"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
