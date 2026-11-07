"""Fail-closed structural consistency check for committed npm and Cargo locks.

Complements (not replaces) npm ci, cargo --locked, SCA and review.
"""
import json
import re
import sys
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def verify_npm(package, lock):
    errors = []
    root = lock.get("packages", {}).get("", {})
    if lock.get("lockfileVersion") != 3 or not isinstance(root, dict):
        return ["package-lock v3 o raíz inválida"]
    for key in ("name", "version", "dependencies", "devDependencies"):
        expected = package.get(key, {} if "Dependencies" in key else "")
        actual = root.get(key, {} if "Dependencies" in key else "")
        if expected != actual:
            errors.append("package.json y package-lock divergen en " + key)
    for path, item in lock.get("packages", {}).items():
        if not path:
            continue
        if not isinstance(item, dict) or item.get("link"):
            errors.append("Dependencia npm no fijada: " + path)
        elif not re.fullmatch(r"sha512-[A-Za-z0-9+/]+={0,2}", item.get("integrity", "")):
            errors.append("SHA512 npm ausente/incorrecto: " + path)
    return errors


def verify_cargo(cargo, lock):
    errors = []
    packages = lock.get("package", [])
    if lock.get("version") != 3 or not isinstance(packages, list) or len(packages) < 2:
        return ["Cargo.lock inválido"]
    root = cargo["package"]
    if not any(p.get("name") == root["name"] and p.get("version") == root["version"]
               for p in packages):
        errors.append("Cargo.lock desalineado con crate raíz")
    seen = set()
    for package in packages:
        ident = (package.get("name"), package.get("version"))
        if ident in seen:
            errors.append("Crate duplicado: " + repr(ident))
        seen.add(ident)
        if package.get("source", "").startswith("registry+") and not re.fullmatch(
            r"[0-9a-f]{64}", package.get("checksum", "")
        ):
            errors.append("Crate sin checksum: " + repr(ident))
    return errors


def check(root=ROOT):
    try:
        with (root / "apps/web/package.json").open(encoding="utf-8") as stream:
            package = json.load(stream)
        with (root / "apps/web/package-lock.json").open(encoding="utf-8") as stream:
            npm_lock = json.load(stream)
        with (root / "core/rust/Cargo.toml").open("rb") as stream:
            cargo = tomllib.load(stream)
        with (root / "core/rust/Cargo.lock").open("rb") as stream:
            cargo_lock = tomllib.load(stream)
    except (ValueError, OSError) as exc:
        return ["Lockfile obligatorio ausente o inválido: " + str(exc)]
    return verify_npm(package, npm_lock) + verify_cargo(cargo, cargo_lock)


if __name__ == "__main__":
    problems = check()
    for problem in problems:
        print("FAIL:", problem, file=sys.stderr)
    if problems:
        sys.exit(1)
    print("PASS: grafos npm/Cargo declarados y checksum presentes")
