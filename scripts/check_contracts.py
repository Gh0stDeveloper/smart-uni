#!/usr/bin/env python3
"""Validación estricta de JSON Schema y fixtures v1 (solo desarrollo/CI)."""

import json
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker

ROOT = Path(__file__).resolve().parents[1] / "packages" / "contracts" / "v1"


def load(name):
    return json.loads((ROOT / name).read_text(encoding="utf-8"))


def check():
    registry = load("registry.json")
    assert registry["contract_version"] == "1.0.0"
    assert registry["legacy_storage_version"] == 1
    assert len(registry["operations"]) == len(set(registry["operations"]))
    assert len(registry["error_codes"]) == len(set(registry["error_codes"]))
    for name, enum_field, values in (
        ("envelope.schema.json", "operation", registry["operations"]),
        ("error.schema.json", "code", registry["error_codes"]),
    ):
        schema = load(name)
        Draft202012Validator.check_schema(schema)
        assert schema["properties"][enum_field]["enum"] == values, name
        assert schema["properties"]["schema_version"]["const"] == registry["contract_version"]
    envelope_schema = load("envelope.schema.json")
    error_schema = load("error.schema.json")
    legacy_schema = load("legacy-json.schema.json")
    Draft202012Validator.check_schema(legacy_schema)
    env = Draft202012Validator(envelope_schema, format_checker=FormatChecker())
    err = Draft202012Validator(error_schema, format_checker=FormatChecker())
    local = Draft202012Validator(legacy_schema, format_checker=FormatChecker())
    env.validate(load("examples/notes-create.json"))
    err.validate(load("examples/error-validation.json"))
    local.validate(load("examples/legacy-store.json"))
    assert not env.is_valid(load("examples/unsupported-version.json"))
    assert not env.is_valid({**load("examples/notes-create.json"), "operation_id": "../invalid"})
    assert not err.is_valid({**load("examples/error-validation.json"), "code": "UNKNOWN"})
    assert not local.is_valid({**load("examples/legacy-store.json"), "version": 2})
    print("Contratos SMART UNI 1.0.0: esquemas y fixtures verificados (JSON Schema 2020-12).")


if __name__ == "__main__":
    check()
