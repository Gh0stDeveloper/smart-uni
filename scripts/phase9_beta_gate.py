"""Manual evidence completeness gate for the controlled beta.

A URL written in JSON is not independent proof. Reviewers must inspect evidence
before marking a check 'passed'; this script does NOT query GitHub or devices.
"""
import argparse
import json
import re
import sys
import os
import urllib.request
import urllib.error
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



def verify_actions_evidence(report: dict, fetch_run=None) -> list[str]:
    """Confirm run identity, success and exact source revision via GitHub API.

    A real GitHub run still does NOT prove physical testing, ethical review,
    cryptographic signatures or that a human actually reviewed the evidence.
    """
    commit = report.get("release_commit")
    if not isinstance(commit, str) or not re.fullmatch(r"[0-9a-f]{40}", commit):
        return ["Falta commit exacto de beta, con 40 dígitos hexadecimales"]
    if fetch_run is None:
        def fetch_run(run_id):
            url = ("https://api.github.com/repos/Gh0stDeveloper/smart-uni/actions/runs/"
                   + str(run_id))
            headers = {"Accept": "application/vnd.github+json",
                       "User-Agent": "smartuni-beta-gate"}
            token = os.environ.get("GITHUB_TOKEN")
            if token:
                headers["Authorization"] = "Bearer " + token
            request = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(request, timeout=12) as response:
                if response.status != 200:
                    raise ValueError("Estado HTTP inesperado")
                return json.load(response)
    failures = []
    seen = {}
    for check, entry in report.get("checks", {}).items():
        if not isinstance(entry, dict) or entry.get("status") != "passed":
            continue
        match = re.fullmatch(
            r"https://github\.com/Gh0stDeveloper/smart-uni/actions/runs/([0-9]+)",
            entry.get("evidence", ""),
        )
        if not match:
            failures.append(f"URL sin estructura de Actions: {check}")
            continue
        run_id = int(match.group(1))
        try:
            if run_id not in seen:
                seen[run_id] = fetch_run(run_id)
            run = seen[run_id]
        except (ValueError, OSError, urllib.error.URLError, KeyError, TimeoutError) as exc:
            failures.append(f"No fue posible verificar run {run_id} para {check}: {type(exc).__name__}")
            continue
        repo = run.get("repository") or {}
        if (run.get("id") != run_id or repo.get("full_name") != "Gh0stDeveloper/smart-uni" or
                run.get("head_branch") != "main" or run.get("head_sha") != commit or
                run.get("status") != "completed" or run.get("conclusion") != "success"):
            failures.append(f"Run {run_id} no coincide con commit/main/resultado aprobado: {check}")
    return failures


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
    live_errors = verify_actions_evidence(report)
    for error in live_errors:
        print("BLOQUEADO:", error, file=sys.stderr)
    if live_errors:
        return 1
    print("Evidencia CI cotejada online; la revisión física/humana sigue siendo obligatoria")
    return 0


if __name__ == "__main__":
    sys.exit(main())
