"""Adaptador del diseño SMART UNI a Tkinter, sin cambios de paleta.

El JSON de escritorio es copia exacta de la fuente canónica del monorepo.
PyInstaller incorpora la copia al ejecutable independiente.
"""

import json
import sys
from pathlib import Path


def load_tokens() -> dict:
    root = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent.parent))
    with (root / "design" / "tokens.json").open("r", encoding="utf-8") as fh:
        return json.load(fh)


TOKENS = load_tokens()
_ROLES = {
    "login_bg": "login_background",
    "aqua": "cta",
    "blue": "primary",
    "ink": "text_primary",
    "muted": "text_muted",
    "form_bg": "registration_background",
    "field": "registration_fields",
    "surface": "white",
    "page": "content_background",
    "pale": "highlight",
    "line": "divider",
    "dark_button": "login_action",
}
COLORS = {role: TOKENS["colors"][token] for role, token in _ROLES.items()}
FONT_TITLE = TOKENS["typography"]["headings"]
FONT_TEXT = TOKENS["typography"]["body"]
