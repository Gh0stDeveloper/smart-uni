#!/usr/bin/env python3
"""Guarda los colores e iconos aprobados, sin dependencia de un servicio Figma."""

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def git_blob(path):
    data = path.read_bytes()
    return hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()


def main():
    shared = ROOT / "packages/design-system"
    identity = json.loads((shared / "identity.json").read_text(encoding="utf-8"))
    canon = (shared / "tokens.json").read_bytes()
    assert canon == (ROOT / "apps/desktop/design/tokens.json").read_bytes()
    tokens = json.loads(canon)
    assert tokens["colors"]["primary"] == "#2B80EC"
    assert tokens["colors"]["cta"] == "#2BB2C4"
    assert tokens["typography"] == {"headings": "Poppins", "body": "Roboto"}
    for role in ("text_primary", "text_muted", "divider"):
        assert role in tokens["colors"]
    for kind in ("original_icon_png", "original_icon_svg"):
        target = identity[kind]
        assert git_blob(ROOT / target["path"]) == target["git_blob_sha1"], kind
    assert identity["layout_guardrails"]["extra_right_sidebar"] is False
    assert identity["figma"]["connection_status"] == "not_configured"
    print("Diseño SMART UNI: tokens y SHA de iconos verificados.")


if __name__ == "__main__":
    main()
