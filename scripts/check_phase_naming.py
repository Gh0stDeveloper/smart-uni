#!/usr/bin/env python3
"""Comprueba que el ROADMAP use exclusivamente títulos numéricos consecutivos."""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ROADMAP = ROOT / "docs" / "ROADMAP.md"

PHASE = re.compile(r"^## ([1-9]\d*) (\S.*)$")
SUBPHASE = re.compile(r"^### ([1-9]\d*)\.([1-9]\d*) (\S.*)$")
NUMERIC_HEADING = re.compile(r"^#{2,3}\s+\d")
LEGACY_HEADING = re.compile(r"^#{2,3}\s+(?:Fase|Subfase)\s+", re.IGNORECASE)
LEGACY_LABEL = re.compile(
    r"\b(?:Fase\s+\d+\s*:|Subfase\s+\d+\.\d+\s*:)", re.IGNORECASE
)
CODE_FENCE = re.compile(r"^\s*(```|~~~)")


def validate_roadmap(content: str) -> list[str]:
    """Verifica que el índice principal y sus subdivisiones no tengan saltos."""
    errors: list[str] = []
    expected_phase = 1
    current_phase: int | None = None
    expected_subphase = 1
    number_of_subphases = 0

    for line_number, line in enumerate(content.splitlines(), 1):
        phase = PHASE.fullmatch(line)
        subphase = SUBPHASE.fullmatch(line)

        if phase:
            if current_phase is not None and number_of_subphases == 0:
                errors.append(f"El apartado {current_phase} no tiene subdivisiones.")

            number = int(phase.group(1))
            if number != expected_phase:
                errors.append(
                    f"ROADMAP:{line_number}: se esperaba {expected_phase}, "
                    f"se encontró {number}."
                )

            current_phase = number
            expected_phase += 1
            expected_subphase = 1
            number_of_subphases = 0

        elif subphase:
            parent = int(subphase.group(1))
            number = int(subphase.group(2))
            if parent != current_phase or number != expected_subphase:
                errors.append(
                    f"ROADMAP:{line_number}: se esperaba "
                    f"{current_phase}.{expected_subphase}, "
                    f"se encontró {parent}.{number}."
                )
            expected_subphase += 1
            number_of_subphases += 1

        elif NUMERIC_HEADING.match(line) or LEGACY_HEADING.match(line):
            errors.append(
                f"ROADMAP:{line_number}: encabezado incorrecto: {line}"
            )

    if current_phase is None:
        errors.append("ROADMAP: no hay apartados principales.")
    elif number_of_subphases == 0:
        errors.append(f"El apartado {current_phase} no tiene subdivisiones.")
    return errors


def validate_files() -> list[str]:
    """Rechaza los identificadores antiguos en la documentación."""
    errors: list[str] = []

    for path in ROOT.rglob("*.md"):
        if any(part in {".git", ".venv", "node_modules"} for part in path.parts):
            continue

        inside_code = False
        fence_type: str | None = None

        for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            match = CODE_FENCE.match(line)
            if match:
                marker = match.group(1)[:3]
                if not inside_code:
                    inside_code, fence_type = True, marker
                elif marker == fence_type:
                    inside_code, fence_type = False, None
                continue

            if inside_code:
                continue

            if LEGACY_HEADING.match(line) or LEGACY_LABEL.search(line):
                errors.append(
                    f"{path.relative_to(ROOT)}:{number}: "
                    "se encontró nomenclatura anterior."
                )

    if not ROADMAP.exists():
        errors.append("No existe docs/ROADMAP.md.")
    else:
        errors.extend(validate_roadmap(ROADMAP.read_text(encoding="utf-8")))

    return errors


if __name__ == "__main__":
    problems = validate_files()
    for problem in problems:
        print("ERROR:", problem)
    print("Numeración:", "CORRECTA" if not problems else "INCORRECTA")
    raise SystemExit(bool(problems))
