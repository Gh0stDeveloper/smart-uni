#!/usr/bin/env python3
"""Comprueba el formato y la secuencia oficial de fases y subfases."""

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ROADMAP = ROOT / "docs" / "ROADMAP.md"
PHASE = re.compile(r"^## Fase ([1-9][0-9]*): (\S.*)$")
SUB = re.compile(r"^### Subfase ([1-9][0-9]*)\.([1-9][0-9]*): (\S.*)$")
HEADING = re.compile(r"^#{1,6}\s+(?:Fase|Subfase)\b")
BAD_CODE = re.compile(r"\b(?:Fase|Subfase)\s+(?:0\b|[A-Z][0-9]*\b)")
FENCE = re.compile(r"^\s*(```|~~~)")


def check_roadmap(source):
    problems = []
    expected_phase = 1
    parent = None
    expected_sub = 1
    subs_in_parent = 0
    for line_no, line in enumerate(source.splitlines(), 1):
        phase, sub = PHASE.fullmatch(line), SUB.fullmatch(line)
        if phase:
            if parent is not None and subs_in_parent == 0:
                problems.append(f"Fase {parent} sin subfases.")
            current = int(phase.group(1))
            if current != expected_phase:
                problems.append(f"ROADMAP:{line_no}: esperado Fase {expected_phase}.")
            parent, expected_phase = current, expected_phase + 1
            expected_sub, subs_in_parent = 1, 0
        if sub:
            p, number = int(sub.group(1)), int(sub.group(2))
            if p != parent or number != expected_sub:
                problems.append(
                    f"ROADMAP:{line_no}: subfase {p}.{number} no corresponde "
                    f"a Fase {parent}, subfase esperada {expected_sub}."
                )
            expected_sub, subs_in_parent = expected_sub + 1, subs_in_parent + 1
    if parent is None:
        problems.append("ROADMAP sin fases oficiales.")
    elif subs_in_parent == 0:
        problems.append(f"Fase {parent} sin subfases.")
    return problems


def check_files():
    problems = []
    for path in ROOT.rglob("*.md"):
        if any(part in {".git", "node_modules", ".venv"} for part in path.parts):
            continue
        fence = None
        for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            m = FENCE.match(line)
            if m:
                marker = m.group(1)[:3]
                if fence is None:
                    fence = marker
                elif fence == marker:
                    fence = None
                continue
            if fence:
                continue
            if HEADING.match(line) and not (PHASE.fullmatch(line) or SUB.fullmatch(line)):
                problems.append(f"{path.relative_to(ROOT)}:{line_no}: encabezado inválido.")
            if BAD_CODE.search(line):
                problems.append(f"{path.relative_to(ROOT)}:{line_no}: numeración no permitida.")

    if not ROADMAP.is_file():
        problems.append("Falta docs/ROADMAP.md.")
    else:
        problems.extend(check_roadmap(ROADMAP.read_text(encoding="utf-8")))
    return problems


if __name__ == "__main__":
    errors = check_files()
    for error in errors:
        print("ERROR:", error)
    print("Validación de fases:", "CORRECTA" if not errors else "FALLIDA")
    raise SystemExit(bool(errors))
