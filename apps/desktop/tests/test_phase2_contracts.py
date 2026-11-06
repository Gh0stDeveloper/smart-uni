"""Contratos versionados: coherencia del registro, IDs y almacenamiento legado."""

import json
import tempfile
import unittest
from pathlib import Path

from smart_uni.core import SmartUniService


ROOT = Path(__file__).resolve().parents[3] / "packages" / "contracts" / "v1"


def read(relative):
    return json.loads((ROOT / relative).read_text(encoding="utf-8"))


class TestSharedContracts(unittest.TestCase):
    def test_registry_and_schema_versions_match(self):
        registry = read("registry.json")
        self.assertEqual(registry["contract_version"], "1.0.0")
        self.assertEqual(registry["legacy_storage_version"], 1)
        self.assertEqual(
            read("envelope.schema.json")["properties"]["operation"]["enum"],
            registry["operations"],
        )
        self.assertEqual(
            read("error.schema.json")["properties"]["code"]["enum"],
            registry["error_codes"],
        )

    def test_fixture_operation_identifiers_and_fields(self):
        msg = read("examples/notes-create.json")
        self.assertEqual(msg["schema_version"], "1.0.0")
        self.assertEqual(msg["operation"], "notes.create")
        self.assertEqual(len(bytes.fromhex(msg["operation_id"])), 16)
        self.assertEqual(len(bytes.fromhex(msg["entity_id"])), 16)
        self.assertTrue(msg["actor_ref"].endswith("@example.edu"))
        self.assertIsInstance(msg["payload"], dict)
        self.assertEqual(read("examples/unsupported-version.json")["schema_version"], "9.0.0")

    def test_schema_documents_are_draft_2020_12(self):
        for name in ("envelope.schema.json", "error.schema.json", "legacy-json.schema.json"):
            schema = read(name)
            self.assertEqual(schema["$schema"], "https://json-schema.org/draft/2020-12/schema")
            self.assertIn("required", schema)
            self.assertIn("type", schema)

    def test_legacy_json_storage_not_migrated(self):
        with tempfile.TemporaryDirectory() as dirname:
            db = SmartUniService(Path(dirname) / "data.json")
            data = db._read()
            schema = read("legacy-json.schema.json")
            self.assertEqual(data["version"], schema["properties"]["version"]["const"])
            self.assertTrue(set(schema["required"]).issubset(data))


if __name__ == "__main__":
    unittest.main()
