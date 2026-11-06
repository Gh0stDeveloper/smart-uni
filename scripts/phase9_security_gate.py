"""Regression gate for known dangerous SMART UNI configurations (not a full SAST).

No network access, credentials or user data. Use alongside Bandit, audits and review.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def check_sources(manifest: str, gradle: str, native: str, auth_config: str) -> list[str]:
    errors: list[str] = []
    for expected in ['android:allowBackup="false"', 'android:usesCleartextTraffic="false"']:
        if expected not in manifest:
            errors.append("AndroidManifest: falta " + expected)
    if 'android:debuggable="true"' in manifest:
        errors.append("AndroidManifest permite depuración")
    for expected in ("minifyEnabled true", "debuggable false", "proguardFiles"):
        if expected not in gradle:
            errors.append("Gradle release: falta " + expected)
    if not re.search(r"targetSdk\s+3[5-9]\b", gradle):
        errors.append("Target SDK no declarado >=35 (revisar política Play vigente)")
    if "https://" not in native or '"/healthz"' not in native:
        errors.append("Adaptador JNI: falta HTTPS explícito /healthz")
    for forbidden in ("SSL_VERIFY_NONE", "setDefaultHostnameVerifier", "setSSLSocketFactory",
                      "TrustAllCerts", "ALLOW_ALL_HOSTNAME_VERIFIER"):
        if forbidden in native:
            errors.append("Adaptador JNI TLS inseguro: " + forbidden)
    if "allow_legacy_plaintext_notes: bool = False" not in auth_config:
        errors.append("Backend: ruta demo plaintext debe estar bloqueada por defecto")
    return errors


def scan(root: Path = ROOT) -> list[str]:
    paths = {
        "manifest": "apps/android/app/src/main/AndroidManifest.xml",
        "gradle": "apps/android/app/build.gradle",
        "native": "apps/android/app/src/main/cpp/bridge.cpp",
        "auth_config": "services/api/app/config.py",
    }
    texts = {}
    errors = []
    for key, relative in paths.items():
        try:
            texts[key] = (root / relative).read_text(encoding="utf-8")
        except OSError:
            errors.append("Archivo obligatorio ausente: " + relative)
    if not errors:
        errors.extend(check_sources(**texts))
    # Search narrowly in shipped source; no false sense of complete secret scanning.
    for relative in (
        paths["manifest"], paths["native"], paths["auth_config"],
        "apps/android/app/src/main/java/xyz/smartuni/app/NativeBridge.java",
    ):
        if not (root / relative).is_file():
            continue
        body = (root / relative).read_text(encoding="utf-8")
        if re.search(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----", body):
            errors.append("Una clave privada aparece en " + relative)
    return errors


if __name__ == "__main__":
    problems = scan()
    for problem in problems:
        print("FAIL", problem, file=sys.stderr)
    if problems:
        sys.exit(1)
    print("PASS: controles estáticos críticos de SMART UNI; NO equivale a auditoría completa")
