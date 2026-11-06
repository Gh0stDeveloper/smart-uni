"""End-to-end SQLCipher/Rust client <-> FastAPI/PostgreSQL over TestClient.

The server sees only authenticated SUAEAD01 ciphertext; all accounts,
passwords, content and AES keys in these tests are synthetic/ephemeral.
"""
import os
import tempfile
from pathlib import Path
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from test_api import setup, headers, make_token
from smart_uni.encrypted_sync import EncryptedSyncClient, SyncAuthError, SyncError
from smart_uni.offline_queue import OfflineOutbox, make_message
from smart_uni.secure_storage import EncryptedSQLiteRepository

INITIAL = {"version": 1, "students": [], "courses": [], "announcements": []}


class MemoryKeys:
    def __init__(self):
        self.keys = {}

    def get(self, identifier):
        return self.keys.get(identifier)

    def put(self, identifier, key):
        self.keys[identifier] = key


class DropAck:
    """Simulates TCP reset *after* successful server commit."""
    def __init__(self, transport):
        self.transport = transport
        self.once = True

    def get(self, *args, **kwargs):
        return self.transport.get(*args, **kwargs)

    def put(self, *args, **kwargs):
        return self.transport.put(*args, **kwargs)

    def post(self, path, **kwargs):
        result = self.transport.post(path, **kwargs)
        if path == "/api/v1/sync/push" and self.once:
            self.once = False
            raise ConnectionResetError("simulated lost server ACK")
        return result


@pytest.fixture
def clients(setup):
    api, engine = setup
    token = make_token("owner-e2e")
    user = api.get("/api/v1/me", headers=headers(token)).json()
    owner_id = user["id"]
    shared_key = os.urandom(32)
    with tempfile.TemporaryDirectory() as directory:
        def make_client(tag, *, transport=None, content_key=None, token_value=None):
            repo = EncryptedSQLiteRepository(
                Path(directory) / (tag + ".sqlcipher"), INITIAL,
                key_store=MemoryKeys(),
            )
            return EncryptedSyncClient(
                repo, owner_id, content_key or shared_key, transport or api,
                bearer_supplier=lambda: token_value or token,
                allow_test_transport=True,
            )
        yield api, token, owner_id, shared_key, make_client


def test_two_devices_incremental_push_pull_history_and_tombstones(clients):
    api, token, owner_id, key, new_client = clients
    a, b = new_client("desktop-win"), new_client("desktop-linux")
    rid = uuid4()
    op = a.queue_change(rid, b"Nota privada original")
    assert a.status()["pending"] == 1
    assert a.push_pending() == [(op, "ack")]
    assert a.status()["acked"] == 1
    assert b.pull_next()["cursor"] == 1
    assert b.history(rid)[0]["plaintext"] == b"Nota privada original"
    second = b.queue_change(rid, b"Nota privada editada", base_revision=1)
    assert b.push_pending() == [(second, "ack")]
    assert a.pull_next()["cursor"] == 2
    assert [h["revision"] for h in a.history(rid)] == [1, 2]
    tombstone = a.queue_change(rid, base_revision=2, deleted=True)
    assert a.push_pending() == [(tombstone, "ack")]
    assert b.pull_next()["cursor"] == 3
    history = b.history(rid)
    assert [h["deleted"] for h in history] == [False, False, True]
    assert history[-1]["plaintext"] is None
    assert b.pull_next()["count"] == 0
    assert b.status()["cursor"] == 3
    assert b"Nota privada" not in a.repo.path.read_bytes()
    assert b"Nota privada" not in b.repo.path.read_bytes()


def test_dropped_ack_and_idempotent_retry_preserves_one_revision(clients):
    api, token, owner_id, key, create = clients
    client = create("lost-ack", transport=DropAck(api))
    rid = uuid4()
    op = client.queue_change(rid, b"Una sola escritura")
    assert client.push_pending() == [(op, "retry_scheduled")]
    assert client.status()["pending"] == 1
    assert api.get("/api/v1/sync/pull", headers=headers(token)).json()["high_watermark"] == 1
    assert client.push_pending() == []  # Backoff persisted until next attempt.
    assert client.push_pending(force=True) == [(op, "ack")]
    assert client.pull_next()["cursor"] == 1
    assert len(client.history(rid)) == 1


def test_conflict_manual_keep_local_reencrypts_new_base(clients):
    api, token, owner_id, key, new_client = clients
    win, lin = new_client("conflict-windows"), new_client("conflict-linux")
    rid = uuid4()
    op_a = win.queue_change(rid, b"Version A sin red")
    op_b = lin.queue_change(rid, b"Version B sin red")
    assert win.push_pending() == [(op_a, "ack")]
    assert lin.push_pending() == [(op_b, "conflict")]
    assert lin.status()["conflicts"] == 1
    fresh = lin.resolve_keep_local(op_b)
    assert fresh != op_b
    assert lin.push_pending() == [(fresh, "ack")]
    assert win.pull_next()["cursor"] == 2
    assert [h["plaintext"] for h in win.history(rid)] == [
        b"Version A sin red", b"Version B sin red",
    ]
    assert api.get("/api/v1/sync/conflicts", headers=headers(token)).json() == []


def test_atomic_cursor_rollback_and_wrong_key_no_partial_accept(clients):
    api, token, owner_id, key, new_client = clients
    writer, reader, wrong = new_client("writer"), new_client("reader"), new_client(
        "wrong-key", content_key=os.urandom(32),
    )
    first = writer.queue_change(uuid4(), b"first")
    second = writer.queue_change(uuid4(), b"second")
    assert len(writer.push_pending()) == 2
    def crash(index):
        if index == 0:
            raise RuntimeError("simulated process crash after first write")
    with pytest.raises(RuntimeError):
        reader.pull_next(failpoint=crash)
    assert reader.status()["cursor"] == 0
    assert reader.pull_next()["cursor"] == 2
    with pytest.raises(SyncError):
        wrong.pull_next()
    assert wrong.status()["cursor"] == 0


def test_identity_mismatch_and_unencrypted_v1_queue_never_uploaded(clients):
    api, token, owner_id, key, new_client = clients
    bad_user = make_token("another-identity")
    wrong = new_client("wrong-owner-login", token_value=bad_user)
    with pytest.raises(SyncAuthError):
        wrong.verify_identity()
    assert wrong.status()["remote_identity_verified"] is False
    client = new_client("legacy-queue-safe")
    original = make_message("notes.create", "legacy@uni.edu", {"content": "unsealed"})
    OfflineOutbox(client.repo).apply(original, lambda doc: doc["announcements"].append(
        {"fecha": "ci", "titulo": "unsealed", "detalle": "synthetic"}
    ))
    assert client.push_pending() == []
    assert api.get("/api/v1/sync/pull", headers=headers(token)).json()["changes"] == []


def test_chunk_resume_remote_download_replays_ciphertext_only(clients):
    api, token, owner_id, key, new_client = clients
    sender, receiver = new_client("blob-sender"), new_client("blob-receiver")
    plaintext = os.urandom(300_000)
    rid = uuid4()
    blob_id = sender.stage_blob(rid, plaintext)
    assert sender.upload_blob(blob_id, max_parts=1)["status"] == "partial"
    assert sender.upload_blob(blob_id)["status"] == "complete"
    op = sender.queue_change(rid, b"ciphertext-only manifest", blob_id=blob_id)
    assert sender.push_pending() == [(op, "ack")]
    assert receiver.pull_next()["cursor"] == 1
    assert receiver.download_blob(blob_id, rid) == plaintext
    # Can reopen and verify cached encrypted chunks without changing the result.
    assert receiver.download_blob(blob_id, rid) == plaintext
    assert plaintext[:64] not in sender.repo.path.read_bytes()
    assert plaintext[:64] not in receiver.repo.path.read_bytes()
