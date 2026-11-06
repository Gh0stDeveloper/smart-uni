#!/usr/bin/env python3
"""Sincronización explícita de los tokens canónicos con los recursos Tkinter."""

import argparse
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "packages/design-system/tokens.json"
DEST = ROOT / "apps/desktop/design/tokens.json"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true", help="Escribir copia después de revisión humana")
    args = parser.parse_args()
    content = SOURCE.read_bytes()
    if args.write:
        DEST.write_bytes(content)
        print("Tokens de escritorio sincronizados con la fuente compartida.")
    elif DEST.read_bytes() != content:
        raise SystemExit("ERROR: tokens desincronizados; revisar fuente y ejecutar --write.")
    else:
        print("Tokens idénticos a la fuente canónica.")


if __name__ == "__main__":
    main()
