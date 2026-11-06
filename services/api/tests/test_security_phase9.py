"""Stage 9 negative HTTP security regression, synthetic identities and Postgres.

Covers representative injection payloads and cross-owner authorization; not a
penetration test. Uses the same real Postgres fixture as phase 5/7.
"""
import base64
from urllib.parse import quote
from uuid import uuid4

import pytest

from test_api import setup, make_token, headers
from test_sync import command, owner, push


@pytest.mark.parametrize("injection", [
    "0 OR 1=1",
    "1;DROP TABLE identities;--",
    "-1 UNION SELECT * FROM notes",
    "' OR 'a'='a",
    "999999999999999999999999999999999999999",
])
def test_sync_cursor_rejects_sql_payloads_before_database(setup, injection):
    client, _ = setup
    token = make_token("phase9-cursor")
    response = client.get("/api/v1/sync/pull?cursor=" + quote(injection, safe=""),
                          headers=headers(token))
    assert response.status_code == 422, response.text
    assert client.get("/api/v1/me", headers=headers(token)).status_code == 200


def test_sync_rejects_foreign_ciphertext_even_with_forged_actor(setup):
    client, _ = setup
    token_a = make_token("phase9-owner-a")
    token_b = make_token("phase9-owner-b")
    rid = uuid4()
    command_a, _, _ = command(owner(client, token_a), rid,
                              plaintext=b"PHASE9_SYNTHETIC_PRIVATE_ONLY")
    assert push(client, token_a, command_a).status_code == 200
    response = client.post("/api/v1/sync/push",
                           headers={**headers(token_b), "X-Actor-Ref": "phase9-owner-a"},
                           json={**command_a, "operation_id": str(uuid4())})
    assert response.status_code == 422, response.text
    assert client.get("/api/v1/sync/pull", headers=headers(token_b)).json()["changes"] == []
    assert len(client.get("/api/v1/sync/pull", headers=headers(token_a)).json()["changes"]) == 1


@pytest.mark.parametrize("invalid", [None, "", "???!", "a" * 10000])
def test_push_rejects_invalid_ciphertext_and_keeps_history(setup, invalid):
    client, _ = setup
    token = make_token("phase9-bad-frame")
    rid = uuid4()
    payload = {
        "operation_id": str(uuid4()),
        "resource_id": str(rid),
        "base_revision": 0,
        "epoch": 1,
        "deleted": False,
        "ciphertext_b64": invalid,
    }
    result = client.post("/api/v1/sync/push", headers=headers(token), json=payload)
    assert result.status_code == 422, result.text
    assert client.get("/api/v1/sync/pull", headers=headers(token)).json()["changes"] == []


def test_push_rejects_forged_owner_role_and_sql_identifier(setup):
    client, _ = setup
    token = make_token("phase9-request-owner")
    actor = owner(client, token)
    payload, _, _ = command(actor, uuid4(), plaintext=b"safe-synthetic")
    payload["owner_id"] = str(uuid4())
    payload["role"] = "admin"
    assert push(client, token, payload).status_code == 422
    del payload["owner_id"]
    del payload["role"]
    payload["resource_id"] = "x' OR 1=1 --"
    assert push(client, token, payload).status_code == 422
