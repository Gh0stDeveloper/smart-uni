"""Lab artifact digest receipt, ZIP verification and fail-closed recheck.

Receipts are NOT signatures, provenance attestations, or release approval.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import re
import sys
import zipfile
from pathlib import Path

LAB_ARTIFACTS = {
    "apk_debug": "apps/android/app/build/outputs/apk/debug/app-debug.apk",
    "apk_release_unsigned": "apps/android/app/build/outputs/apk/release/app-release-unsigned.apk",
    "aab_release_unsigned": "apps/android/app/build/outputs/bundle/release/app-release.aab",
}
MAX_ARTIFACT_BYTES = 256 * 1024 * 1024


class ArtifactRejected(ValueError):
    pass


def inspect_file(path: Path) -> dict:
    if not path.is_file() or path.stat().st_size < 100:
        raise ArtifactRejected("Artefacto ausente o vacío")
    if path.stat().st_size > MAX_ARTIFACT_BYTES:
        raise ArtifactRejected("Artefacto supera el límite de laboratorio")
    if not zipfile.is_zipfile(path):
        raise ArtifactRejected("Artefacto no es ZIP APK/AAB válido")
    with zipfile.ZipFile(path) as archive:
        names = archive.namelist()
        if not names or len(set(names)) != len(names):
            raise ArtifactRejected("ZIP contiene nombres duplicados o está vacío")
        for name in names:
            parts = name.replace("\\", "/").split("/")
            if name.startswith("/") or ".." in parts:
                raise ArtifactRejected("Ruta ZIP insegura")
        if archive.testzip() is not None:
            raise ArtifactRejected("CRC ZIP incorrecto")
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return {"bytes": path.stat().st_size, "sha256": digest.hexdigest()}


def build_receipt(root: Path, sha: str, paths=None) -> dict:
    if not re.fullmatch(r"[0-9a-f]{40}", sha):
        raise ArtifactRejected("SHA de commit obligatorio y válido")
    paths = LAB_ARTIFACTS if paths is None else paths
    records = {name: inspect_file(root / rel) for name, rel in paths.items()}
    return {
        "schema_version": 1,
        "git_commit": sha,
        "release_approved": False,
        "signing_status": "LAB_ONLY_DEBUG_SIGNED_RELEASE_UNSIGNED",
        "files": records,
    }


def verify_receipt(root: Path, receipt: dict, paths=None) -> None:
    if not isinstance(receipt, dict) or set(receipt) != {
        "schema_version", "git_commit", "release_approved", "signing_status", "files"
    }:
        raise ArtifactRejected("Recibo con esquema desconocido")
    if receipt.get("schema_version") != 1 or receipt.get("release_approved") is not False:
        raise ArtifactRejected("Recibo intenta aprobar release")
    if receipt.get("signing_status") != "LAB_ONLY_DEBUG_SIGNED_RELEASE_UNSIGNED":
        raise ArtifactRejected("Estado de firmas no admitido")
    expected = build_receipt(root, receipt.get("git_commit", ""), paths)
    if expected != receipt:
        raise ArtifactRejected("SHA256 o tamaño distinto: artefacto modificado")


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=("create", "verify"))
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--sha", default="")
    parser.add_argument("--receipt", required=True, type=Path)
    args = parser.parse_args(argv)
    try:
        if args.action == "create":
            receipt = build_receipt(args.root, args.sha)
            args.receipt.parent.mkdir(parents=True, exist_ok=True)
            args.receipt.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
        else:
            receipt = json.loads(args.receipt.read_text(encoding="utf-8"))
            verify_receipt(args.root, receipt)
    except (ValueError, OSError, zipfile.BadZipFile) as exc:
        print("FAIL:", exc, file=sys.stderr)
        return 1
    print("PASS: SHA256, longitud y ZIP verificados; NO equivale a firma digital")
    return 0


if __name__ == "__main__":
    sys.exit(main())
