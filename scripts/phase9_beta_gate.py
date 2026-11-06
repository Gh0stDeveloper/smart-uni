"""Manual evidence completeness gate for the controlled beta.

A URL written in JSON is not independent proof. Reviewers must inspect evidence
before marking a check 'passed'; this script does NOT query GitHub or devices.
"""
import argparse
import json
import re
import sys
from pathlib import Path

REQUIRED_CHECKS = (
    "android_instrumentation",
    "android_physical",
    "android_keystore_recovery",
    "windows_linux_secure_storage",
    "real_oidc_pkce",
    "cross_device_sync",
    "encrypted_backup_restore",
    "key_rotation_revocation",
    "signed_release_artifacts",
    "update_rollback_verified",
    "security_findings_triaged",
    "accessibility_mobile",
)


def validate_beta_report(report: dict) -> list[str]:
    errors = []
    if not isinstance(report, dict) or report.get("schema_version") != 1:
        return ["Esquema beta inválido"]
    checks = report.get("checks")
    if not isinstance(checks, dict):
        return ["Faltan verificaciones"]
    for name in REQUIRED_CHECKS:
        entry = checks.get(name)
        if not isinstance(entry, dict) or entry.get("status") != "passed":
            errors.append("Sin evidencia aprobada: " + name)
            continue
        url = entry.get("evidence")
        if not isinstance(url, str) or not re.fullmatch(
            r"https://github\.com/Gh0stDeveloper/smart-uni/actions/runs/[0-9]+",
            url,
        ):
            errors.append("Evidencia CI inválida o no vinculada: " + name)
        if not isinstance(entry.get("reviewed_by"), str) or not entry["reviewed_by"].strip():
            errors.append("Sin revisión humana: " + name)
    if report.get("blocking_critical_findings") != 0:
        errors.append("Existen hallazgos críticos no resueltos o sin evaluación")
    if report.get("publication_approval") is not True:
        errors.append("No existe aprobación explícita para beta controlada")
    return errors


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("report", type=Path)
    args = parser.parse_args(argv)
    try:
        report = json.loads(args.report.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        print("DENEGADO: no se puede leer reporte beta", exc, file=sys.stderr)
        return 1
    errors = validate_beta_report(report)
    for error in errors:
        print("BLOQUEADO:", error, file=sys.stderr)
    if errors:
        return 1
    print("Checklist completa (requiere cotejo humano independiente)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
