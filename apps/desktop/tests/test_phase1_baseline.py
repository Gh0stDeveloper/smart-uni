"""Regresión de la etapa 1: datos sintéticos, sin modificar el producto."""

import hashlib
import json
import shutil
import tempfile
import unittest
from pathlib import Path

from smart_uni.core import SmartUniService, ValidationError, seed_demo
from smart_uni.student_data import StudentSpaceService, SUBJECTS
from smart_uni.ui import COLORS


ROOT = Path(__file__).resolve().parents[1]


class TestPhase1Baseline(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.addCleanup(self.folder.cleanup)
        self.path = Path(self.folder.name) / "data.json"
        self.db = SmartUniService(self.path)

    def test_icon_original_and_design_tokens_preserved(self):
        icon = ROOT / "design" / "previews" / "00_isotipo_smart_uni.png"
        svg = ROOT / "design" / "figma_svg" / "00_isotipo_smart_uni.svg"
        tokens = json.loads((ROOT / "design" / "tokens.json").read_text(encoding="utf-8"))
        shared = json.loads(
            (ROOT.parents[1] / "packages" / "design-system" / "tokens.json")
            .read_text(encoding="utf-8")
        )
        self.assertEqual(icon.read_bytes()[:8], b"\x89PNG\r\n\x1a\n")
        self.assertIn("<svg", svg.read_text(encoding="utf-8"))
        self.assertEqual(tokens, shared)
        self.assertEqual(COLORS["blue"], tokens["colors"]["primary"])
        self.assertEqual(COLORS["aqua"], tokens["colors"]["cta"])

    def test_legacy_json_is_read_without_spaces_migration(self):
        self.assertEqual(self.db._read()["version"], 1)
        self.assertNotIn("student_spaces", self.db._read())
        seed_demo(self.db)
        self.assertEqual(StudentSpaceService(self.db).overview("demo@smartuni.edu")["tasks"], [])

    def test_demo_is_idempotent(self):
        seed_demo(self.db)
        seed_demo(self.db)
        students = self.db._read()["students"]
        self.assertEqual([s["email"] for s in students], ["demo@smartuni.edu"])

    def test_student_flow_isolation_and_persistence(self):
        seed_demo(self.db)
        self.db.register("Prueba Estudiante", "otro@uni.edu", "Ingeniería", "UnaClaveDePrueba123")
        space = StudentSpaceService(self.db)
        note = space.add_note("demo@smartuni.edu", "Nota de prueba", SUBJECTS[0], "Texto simulado")
        self.assertNotIn(note, space.overview("otro@uni.edu")["notes"])
        reopened = StudentSpaceService(SmartUniService(self.path))
        self.assertEqual(reopened.overview("demo@smartuni.edu")["notes"][0]["id"], note["id"])
        self.assertIsNotNone(reopened.base.authenticate("otro@uni.edu", "UnaClaveDePrueba123"))

    def test_corrupted_json_is_not_overwritten_on_read(self):
        self.path.write_text("{json corrupto", encoding="utf-8")
        reopened = SmartUniService(self.path)
        with self.assertRaises(RuntimeError):
            reopened.courses()
        self.assertEqual(self.path.read_text(encoding="utf-8"), "{json corrupto")

    def test_failed_serialization_keeps_previous_json(self):
        original = self.path.read_bytes()
        with self.assertRaises(TypeError):
            self.db._write({"students": {1, 2}})
        self.assertEqual(self.path.read_bytes(), original)
        self.assertEqual(list(self.path.parent.glob(".smartuni-*.json")), [])

    def test_material_copy_and_delete_without_source(self):
        seed_demo(self.db)
        space = StudentSpaceService(self.db)
        original = self.path.parent / "nota.md"
        original.write_text("Material puramente sintético", encoding="utf-8")
        item = space.add_material("demo@smartuni.edu", SUBJECTS[0], str(original))
        stored = space.material_path("demo@smartuni.edu", item["id"])
        original.unlink()
        self.assertEqual(stored.read_text(encoding="utf-8"), "Material puramente sintético")
        self.assertTrue(space.delete_material("demo@smartuni.edu", item["id"]))
        self.assertFalse(stored.exists())

    def test_material_extension_and_size_limits(self):
        seed_demo(self.db)
        space = StudentSpaceService(self.db)
        invalid = self.path.parent / "archivo.exe"
        invalid.write_bytes(b"MZ")
        with self.assertRaises(ValidationError):
            space.add_material("demo@smartuni.edu", SUBJECTS[0], str(invalid))
        large = self.path.parent / "archivo.txt"
        with large.open("wb") as fh:
            fh.truncate(30 * 1024 * 1024 + 1)
        with self.assertRaises(ValidationError):
            space.add_material("demo@smartuni.edu", SUBJECTS[0], str(large))

    def test_synthetic_backup_can_be_restored(self):
        seed_demo(self.db)
        space = StudentSpaceService(self.db)
        space.add_task("demo@smartuni.edu", "Tarea sintética", SUBJECTS[0], "2026-11-20")
        original = self.path.read_bytes()
        backup = self.path.parent / "respaldo-sintetico.json"
        shutil.copy2(self.path, backup)
        expected_sha256 = hashlib.sha256(original).hexdigest()
        self.assertEqual(hashlib.sha256(backup.read_bytes()).hexdigest(), expected_sha256)
        self.path.unlink()
        shutil.copy2(backup, self.path)
        reopened = SmartUniService(self.path)
        self.assertIsNotNone(reopened.authenticate("demo@smartuni.edu", "Demo1234!"))
        self.assertEqual(
            StudentSpaceService(reopened).overview("demo@smartuni.edu")["tasks"][0]["title"],
            "Tarea sintética",
        )


if __name__ == "__main__":
    unittest.main()
