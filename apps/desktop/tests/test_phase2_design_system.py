"""Regresión del contrato visual SMART UNI, sin capturas inventadas."""

import hashlib
import json
import unittest
from pathlib import Path

from smart_uni.design_system import COLORS, FONT_TITLE, FONT_TEXT, TOKENS
from smart_uni.ui import SmartUniApp, COLORS as UI_COLORS, FONT_TITLE as UI_FONT_TITLE

ROOT = Path(__file__).resolve().parents[3]


class TestDesignSystem(unittest.TestCase):
    def test_palette_exactly_matches_baseline(self):
        self.assertEqual(COLORS, {
            "login_bg": "#91C8F0",
            "aqua": "#2BB2C4",
            "blue": "#2B80EC",
            "ink": "#243448",
            "muted": "#65768C",
            "form_bg": "#D3D3D3",
            "field": "#8ACDF7",
            "surface": "#FFFFFF",
            "page": "#F3F7FC",
            "pale": "#D8EBFD",
            "line": "#E2E8F0",
            "dark_button": "#333333",
        })
        self.assertIs(COLORS, UI_COLORS)

    def test_typography_and_tokens_are_preserved(self):
        self.assertEqual((FONT_TITLE, FONT_TEXT), ("Poppins", "Roboto"))
        self.assertEqual(UI_FONT_TITLE, "Poppins")
        self.assertEqual(TOKENS["figma_canvas"], {"width": 1440, "height": 900})
        self.assertEqual(
            (ROOT / "packages/design-system/tokens.json").read_bytes(),
            (ROOT / "apps/desktop/design/tokens.json").read_bytes(),
        )

    def test_original_icon_blobs_and_navigation_methods(self):
        identity = json.loads(
            (ROOT / "packages/design-system/identity.json").read_text(encoding="utf-8")
        )
        for key in ("original_icon_png", "original_icon_svg"):
            item = identity[key]
            content = (ROOT / item["path"]).read_bytes()
            self.assertEqual(
                hashlib.sha1(b"blob " + str(len(content)).encode() + b"\0" + content).hexdigest(),
                item["git_blob_sha1"],
            )
        for method in ("show_login", "show_register", "show_dashboard",
                       "show_courses", "show_schedule", "show_announcements",
                       "show_student_space"):
            self.assertTrue(callable(getattr(SmartUniApp, method)))
        self.assertTrue(identity["layout_guardrails"]["single_left_navigation"])
        self.assertFalse(identity["layout_guardrails"]["extra_right_sidebar"])


if __name__ == "__main__":
    unittest.main()
