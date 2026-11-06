"""PostgreSQL integration: ciphertext-only sync, OCC conflict preservation and chunk resume.

All plaintext is synthetic, encrypted on the test CLIENT before HTTP.
The server never receives a decryption key or plaintext via sync endpoints.
"""
import base64
import hashlib
import math
import os
from concurrent.futures import ThreadPoolExecutor
from uuid import UUID, uuid4

import pytest
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from sqlalchemy import select
from sqlalchemy.orm import Session

from test_api import setup, make_token, headers
from services.api.app.sync_models import (
    SyncBlobPart, SyncConflict, SyncOwnerState, SyncResource, SyncVersion,
)

CHUNK_SIZE = 128 * 1024


def owner(client, token):
    reply = client.get("/api/v1/me", headers=headers(token))
    assert reply.status_code == 200, reply.text
    return UUID(reply.json()["id"])


def envelope(secret: bytes, owner_id: UUID, resource_id: UUID, plaintext: bytes,
             epoch=1, base=0, kind="put") -> bytes:
    ctx = (f"sync/{owner_id.hex}/{resource_id.hex}/epoch-{epoch}"
           f"/base-{base}/kind-{kind}").encode("ascii")
    nonce = os.urandom(12)
    header = b"SUAEAD01" + b"\x01" + len(ctx).to_bytes(2, "big") + nonce + ctx
    return header + AESGCM(secret).encrypt(nonce, plaintext, header)


def command(owner_id, rid, *, opid=None, base=0, deleted=False, plaintext=b"synthetic-enc",
            key=None, epoch=1, blob_id=None, conflict_id=None):
    key = key or AESGCM.generate_key(bit_length=256)
    blob = envelope(key, owner_id, rid,
                    b"tombstone:v1" if deleted else plaintext, epoch, base,
                    "delete" if deleted else "put")
    data = {
        "operation_id": str(opid or uuid4()),
        "resource_id": str(rid),
        "base_revision": base, "epoch": epoch, "deleted": deleted,
        "ciphertext_b64": base64.b64encode(blob).decode("ascii"),
    }
    if blob_id is not None:
        data["blob_id"] = str(blob_id)
    if conflict_id is not None:
        data["resolve_conflict_id"] = str(conflict_id)
    return data, key, blob


def push(client, token, data):
    return client.post("/api/v1/sync/push", headers=headers(token), json=data)


def test_incremental_cursor_idempotency_owner_isolation_and_no_plaintext(setup):
    client, engine = setup
    a, b = make_token("sync-a"), make_token("sync-b")
    owner_a = owner(client, a)
    rid = uuid4()
    cmd, key, blob = command(owner_a, rid, plaintext=b"PRIVATE_SYNTHETIC_SYNC_CONTENT")
    assert b"PRIVATE_SYNTHETIC_SYNC_CONTENT" not in blob
    result = push(client, a, cmd)
    assert result.status_code == 200, result.text
    first = result.json()
    assert first["status"] == "ack" and first["revision"] == 1 and first["cursor"] == 1
    duplicate = push(client, a, cmd)
    assert duplicate.status_code == 200 and duplicate.json()["duplicate"]
    assert client.get("/api/v1/sync/pull", headers=headers(b)).json()["changes"] == []
    request = client.get("/api/v1/sync/pull?cursor=0&limit=1", headers=headers(a))
    assert request.status_code == 200
    payload = request.json()
    assert payload["cursor"] == 1 and payload["high_watermark"] == 1
    assert len(payload["changes"]) == 1
    candidate = base64.b64decode(payload["changes"][0]["ciphertext_b64"])
    size = int.from_bytes(candidate[9:11], "big")
    assert AESGCM(key).decrypt(candidate[11:23], candidate[23 + size:], candidate[:23 + size]) == (
        b"PRIVATE_SYNTHETIC_SYNC_CONTENT"
    )
    assert client.get("/api/v1/sync/pull?cursor=1", headers=headers(a)).json()["changes"] == []
    # Otro usuario no puede reenviar exactamente el ciphertext de A: AAD une propietario.
    outsider = {**cmd, "operation_id": str(uuid4())}
    assert push(client, b, outsider).status_code == 422
    with Session(engine) as session:
        row = session.scalar(select(SyncVersion).where(SyncVersion.owner_id == owner_a))
        assert row.ciphertext == blob and b"PRIVATE_SYNTHETIC_SYNC_CONTENT" not in row.ciphertext
        assert session.query(SyncVersion).filter_by(owner_id=owner_a).count() == 1


def test_conflict_versions_manual_resolution_tombstones_and_full_history(setup):
    client, engine = setup
    token = make_token("conflict-owner")
    uid = owner(client, token)
    rid = uuid4()
    initial, _, _ = command(uid, rid, plaintext=b"version alpha")
    assert push(client, token, initial).json()["revision"] == 1
    incoming, _, _ = command(uid, rid, base=0, plaintext=b"version offline beta")
    conflict = push(client, token, incoming)
    assert conflict.status_code == 409, conflict.text
    body = conflict.json()
    assert body["status"] == "conflict" and body["server_revision"] == 1
    repeated = push(client, token, incoming)
    assert repeated.status_code == 409 and repeated.json()["conflict_id"] == body["conflict_id"]
    conflicts = client.get("/api/v1/sync/conflicts", headers=headers(token)).json()
    assert len(conflicts) == 1 and conflicts[0]["ciphertext_b64"] == incoming["ciphertext_b64"]
    # Resolver es una operación nueva con base actual y decisión explícita del cliente.
    resolved, _, _ = command(uid, rid, base=1, plaintext=b"version elegida por usuario",
                             conflict_id=UUID(body["conflict_id"]))
    done = push(client, token, resolved)
    assert done.status_code == 200 and done.json()["revision"] == 2
    assert client.get("/api/v1/sync/conflicts", headers=headers(token)).json() == []
    deleted, _, _ = command(uid, rid, base=2, deleted=True)
    assert push(client, token, deleted).json()["revision"] == 3
    pages = []
    cursor = 0
    for _ in range(3):
        page = client.get(f"/api/v1/sync/pull?cursor={cursor}&limit=1",
                          headers=headers(token)).json()
        pages.extend(page["changes"])
        cursor = page["cursor"]
    assert [p["revision"] for p in pages] == [1, 2, 3]
    assert [p["deleted"] for p in pages] == [False, False, True]
    assert pages[-1]["ciphertext_b64"] is not None
    with Session(engine) as session:
        resource = session.get(SyncResource, (uid, rid))
        assert resource.revision == 3 and resource.deleted
        assert session.query(SyncVersion).filter_by(owner_id=uid).count() == 3
        assert session.query(SyncConflict).filter_by(owner_id=uid).count() == 1


def test_operation_id_reuse_with_different_payload_fails(setup):
    client, engine = setup
    token = make_token("reused-id")
    uid = owner(client, token)
    rid = uuid4()
    first, _, _ = command(uid, rid)
    assert push(client, token, first).status_code == 200
    altered, _, _ = command(uid, rid, opid=UUID(first["operation_id"]), base=1, plaintext=b"other")
    assert push(client, token, altered).status_code == 409
    assert client.get("/api/v1/sync/pull", headers=headers(token)).json()["high_watermark"] == 1


def test_ciphertext_only_rejects_plaintext_wrong_context_and_missing_auth(setup):
    client, _ = setup
    token = make_token("frame-owner")
    uid = owner(client, token)
    rid = uuid4()
    cmd, _, _ = command(uid, rid)
    assert client.post("/api/v1/sync/push", json=cmd).status_code == 401
    bad = {**cmd, "ciphertext_b64": base64.b64encode(b"raw plaintext").decode()}
    assert push(client, token, bad).status_code == 422
    wrong_owner, _, _ = command(uuid4(), rid)
    assert push(client, token, wrong_owner).status_code == 422
    assert push(client, token, {**cmd, "ciphertext_b64": "***notbase64***"}).status_code == 422
    assert push(client, token, {**cmd, "epoch": 2}).status_code == 422
    assert client.get("/api/v1/sync/pull", headers=headers(token)).json()["changes"] == []


def test_out_of_order_resumable_blob_checksum_and_cross_user_access(setup):
    client, engine = setup
    token, other = make_token("blob-owner"), make_token("blob-outsider")
    uid = owner(client, token)
    rid, blobid = uuid4(), uuid4()
    key = AESGCM.generate_key(bit_length=256)
    plaintext = os.urandom(2 * CHUNK_SIZE + 22000)
    ciphertext = envelope(key, uid, rid, plaintext, kind="blob")
    digest = hashlib.sha256(ciphertext).hexdigest()
    info = {"blob_id": str(blobid), "resource_id": str(rid),
            "epoch": 1, "base_revision": 0, "total_size": len(ciphertext), "sha256": digest}
    init = client.post("/api/v1/sync/blobs/init", headers=headers(token), json=info)
    assert init.status_code == 200, init.text
    assert init.json()["received_parts"] == []
    parts = [ciphertext[i:i + CHUNK_SIZE] for i in range(0, len(ciphertext), CHUNK_SIZE)]
    assert len(parts) == 3
    def upload(index, payload, token=token):
        return client.put(f"/api/v1/sync/blobs/{blobid}/parts/{index}", content=payload,
            headers={**headers(token), "X-Chunk-Sha256": hashlib.sha256(payload).hexdigest()})
    assert upload(2, parts[2]).status_code == 200
    assert client.post(f"/api/v1/sync/blobs/{blobid}/complete", headers=headers(token)).status_code == 409
    resumed = client.post("/api/v1/sync/blobs/init", headers=headers(token), json=info)
    assert resumed.status_code == 200 and resumed.json()["received_parts"] == [2]
    assert upload(2, parts[2]).json()["duplicate"]
    assert upload(2, b"a" * len(parts[2])).status_code == 409
    assert upload(1, parts[1]).status_code == 200
    assert upload(0, parts[0]).status_code == 200
    assert client.post(f"/api/v1/sync/blobs/{blobid}/complete", headers=headers(token)).status_code == 200
    assert client.post(f"/api/v1/sync/blobs/{blobid}/complete", headers=headers(token)).status_code == 200
    raw = client.get(f"/api/v1/sync/blobs/{blobid}", headers=headers(token))
    assert raw.status_code == 200 and raw.content == ciphertext
    assert raw.headers["X-Content-Sha256"] == digest
    part = client.get(f"/api/v1/sync/blobs/{blobid}/parts/2", headers=headers(token))
    assert part.content == parts[2]
    assert client.get(f"/api/v1/sync/blobs/{blobid}", headers=headers(other)).status_code == 404
    assert client.get(f"/api/v1/sync/blobs/{blobid}/parts/0", headers=headers(other)).status_code == 404
    cmd, _, _ = command(uid, rid, blob_id=blobid)
    result = push(client, token, cmd)
    assert result.status_code == 200, result.text
    assert client.get("/api/v1/sync/pull", headers=headers(token)).json()["changes"][0]["blob_id"] == str(blobid)
    with Session(engine) as session:
        ciphertext_in_db = b"".join(row.data for row in session.scalars(
            select(SyncBlobPart).where(SyncBlobPart.blob_id == blobid).order_by(SyncBlobPart.part_index)
        ))
        assert ciphertext_in_db == ciphertext
        assert plaintext[:40] not in ciphertext_in_db


def test_corrupt_blob_rejected_without_completion(setup):
    client, _ = setup
    token = make_token("corrupt-blob")
    uid = owner(client, token)
    rid, blobid = uuid4(), uuid4()
    secret = AESGCM.generate_key(bit_length=256)
    ciphertext = envelope(secret, uid, rid, b"file data", kind="blob")
    info = {"blob_id": str(blobid), "resource_id": str(rid),
            "epoch": 1, "base_revision": 0, "total_size": len(ciphertext), "sha256": "0" * 64}
    assert client.post("/api/v1/sync/blobs/init", headers=headers(token), json=info).status_code == 200
    headers2 = {**headers(token), "X-Chunk-Sha256": hashlib.sha256(ciphertext).hexdigest()}
    assert client.put(f"/api/v1/sync/blobs/{blobid}/parts/0",
                      content=ciphertext, headers=headers2).status_code == 200
    assert client.post(f"/api/v1/sync/blobs/{blobid}/complete", headers=headers(token)).status_code == 422
    assert client.get(f"/api/v1/sync/blobs/{blobid}", headers=headers(token)).status_code == 404


def test_concurrent_clients_cas_preserves_one_winner_and_conflict(setup):
    client, engine = setup
    token = make_token("concurrent-sync")
    uid = owner(client, token)
    rid = uuid4()
    one, _, _ = command(uid, rid, base=0, plaintext=b"A")
    two, _, _ = command(uid, rid, base=0, plaintext=b"B")
    with ThreadPoolExecutor(max_workers=2) as executor:
        results = list(executor.map(lambda data: push(client, token, data), [one, two]))
    assert sorted(r.status_code for r in results) == [200, 409], [r.text for r in results]
    with Session(engine) as session:
        assert session.query(SyncVersion).filter_by(owner_id=uid).count() == 1
        assert session.query(SyncConflict).filter_by(owner_id=uid).count() == 1
    assert client.get("/api/v1/sync/pull", headers=headers(token)).json()["high_watermark"] == 1
