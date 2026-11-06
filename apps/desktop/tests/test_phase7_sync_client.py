"""Stage 7 native client tests on Windows and Linux, with synthetic offline server."""
import base64
import os
import tempfile
import unittest
from pathlib import Path
from urllib.parse import parse_qs, urlsplit
from uuid import uuid4

from smart_uni.encrypted_sync import EncryptedSyncClient, SyncAuthError, SyncError
from smart_uni.secure_storage import EncryptedSQLiteRepository

try:
    import sqlcipher3
    HAVE_SQLCIPHER = True
except ImportError:
    HAVE_SQLCIPHER = False

INITIAL = {"version": 1, "students": [], "courses": [], "announcements": []}


class MemoryKeys:
    def __init__(self):
        self.values = {}

    def get(self, name):
        return self.values.get(name)

    def put(self, name, data):
        self.values[name] = data


class Reply:
    def __init__(self, code, data):
        self.status_code = code
        self.payload = data

    def json(self):
        return self.payload


class FakeServer:
    """Keeps ciphertext only; never sees content key or plaintext."""
    def __init__(self, owner):
        self.owner = owner
        self.log = []
        self.revisions = {}
        self.seen = {}
        self.conflicts = {}
        self.drop_next_ack = False

    def get(self, path, *, headers):
        if headers.get("Authorization") != "Bearer synthetic-token-for-tests":
            return Reply(401, {})
        if path == "/api/v1/me":
            return Reply(200, {"id": str(self.owner), "role": "student"})
        if path.startswith("/api/v1/sync/pull"):
            query = parse_qs(urlsplit(path).query)
            cursor = int(query.get("cursor", ["0"])[0])
            limit = int(query.get("limit", ["30"])[0])
            changes = [row for row in self.log if row["cursor"] > cursor][:limit]
            return Reply(200, {
                "cursor": changes[-1]["cursor"] if changes else cursor,
                "changes": changes,
                "high_watermark": len(self.log),
                "has_more": len(self.log) > cursor + len(changes),
            })
        return Reply(404, {})

    def post(self, path, *, headers, json=None):
        if headers.get("Authorization") != "Bearer synthetic-token-for-tests":
            return Reply(401, {})
        if path.startswith("/api/v1/sync/conflicts/") and path.endswith("/dismiss"):
            return Reply(200, {"status": "dismissed"})
        if path != "/api/v1/sync/push":
            return Reply(404, {})
        data = json
        opid = data["operation_id"]
        rid = data["resource_id"]
        if opid in self.seen:
            return Reply(200, {**self.seen[opid], "duplicate": True})
        previous = self.revisions.get(rid, 0)
        if data["base_revision"] != previous:
            entry = self.conflicts.setdefault(opid, {
                "status": "conflict", "operation_id": opid,
                "conflict_id": str(uuid4()), "server_revision": previous,
            })
            return Reply(409, entry)
        frame = base64.b64decode(data["ciphertext_b64"])
        if frame[:8] != b"SUAEAD01":
            return Reply(422, {})
        self.revisions[rid] = previous + 1
        cursor = len(self.log) + 1
        self.log.append({
            "cursor": cursor, "operation_id": opid, "resource_id": rid,
            "revision": previous + 1, "epoch": data["epoch"],
            "deleted": data["deleted"], "blob_id": None,
            "ciphertext_b64": data["ciphertext_b64"],
        })
        response = {
            "status": "ack", "operation_id": opid, "resource_id": rid,
            "revision": previous + 1, "cursor": cursor, "duplicate": False,
        }
        self.seen[opid] = response
        if self.drop_next_ack:
            self.drop_next_ack = False
            raise ConnectionResetError("lost ACK after commit")
        return Reply(200, response)


@unittest.skipUnless(HAVE_SQLCIPHER and os.environ.get("SMARTUNI_NATIVE_LIB"),
                     "Requires real SQLCipher and Rust native library")
class TestNativeOfflineSync(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.owner = uuid4()
        self.key = os.urandom(32)
        self.server = FakeServer(self.owner)

    def client(self, tag, **kwargs):
        store = EncryptedSQLiteRepository(
            self.root / (tag + ".sqlcipher"), INITIAL, key_store=MemoryKeys(),
        )
        return EncryptedSyncClient(
            store, self.owner, kwargs.get("key", self.key),
            self.server, bearer_supplier=lambda: "synthetic-token-for-tests",
            allow_test_transport=True,
        )

    def test_two_clients_encrypt_exchange_and_keep_versions(self):
        win, linux = self.client("windows"), self.client("linux")
        rid = uuid4()
        first = win.queue_change(rid, b"SYNTHETIC_SECRET_TEXT")
        self.assertEqual(win.push_pending(), [(first, "ack")])
        self.assertEqual(linux.pull_next()["cursor"], 1)
        self.assertEqual(linux.history(rid)[0]["plaintext"], b"SYNTHETIC_SECRET_TEXT")
        self.assertNotIn(b"SYNTHETIC_SECRET_TEXT", win.repo.path.read_bytes())
        second = linux.queue_change(rid, b"edit", base_revision=1)
        self.assertEqual(linux.push_pending(), [(second, "ack")])
        self.assertEqual(win.pull_next()["cursor"], 2)
        self.assertEqual([v["revision"] for v in win.history(rid)], [1, 2])

    def test_ack_lost_at_least_once_does_not_duplicate_server(self):
        client = self.client("retry")
        op = client.queue_change(uuid4(), b"retry-fake")
        self.server.drop_next_ack = True
        self.assertEqual(client.push_pending(), [(op, "retry_scheduled")])
        self.assertEqual(len(self.server.log), 1)
        self.assertEqual(client.status()["pending"], 1)
        self.assertEqual(client.push_pending(force=True), [(op, "ack")])
        self.assertEqual(len(self.server.log), 1)

    def test_atomic_cursor_after_crash_and_wrong_key(self):
        writer, receiver, wrong = self.client("author"), self.client("reader"), self.client(
            "wrong", key=os.urandom(32),
        )
        writer.queue_change(uuid4(), b"A")
        writer.queue_change(uuid4(), b"B")
        self.assertEqual(len(writer.push_pending()), 2)
        def crash(index):
            if index == 0:
                raise RuntimeError("crash")
        with self.assertRaisesRegex(RuntimeError, "crash"):
            receiver.pull_next(failpoint=crash)
        self.assertEqual(receiver.status()["cursor"], 0)
        self.assertEqual(receiver.pull_next()["cursor"], 2)
        with self.assertRaises(SyncError):
            wrong.pull_next()
        self.assertEqual(wrong.status()["cursor"], 0)

    def test_conflict_retains_candidate_and_manual_local_choice(self):
        a, b = self.client("a"), self.client("b")
        rid = uuid4()
        first = a.queue_change(rid, b"A")
        second = b.queue_change(rid, b"B")
        self.assertEqual(a.push_pending(), [(first, "ack")])
        self.assertEqual(b.push_pending(), [(second, "conflict")])
        self.assertEqual(b.status()["conflicts"], 1)
        replacement = b.resolve_keep_local(second)
        self.assertEqual(b.push_pending(), [(replacement, "ack")])
        self.assertEqual(a.pull_next()["cursor"], 2)
        self.assertEqual([v["plaintext"] for v in a.history(rid)], [b"A", b"B"])

    def test_authenticated_tombstone_and_fail_closed_frame(self):
        writer, reader = self.client("deletion"), self.client("deletion-reader")
        rid = uuid4()
        writer.queue_change(rid, b"exists")
        writer.push_pending()
        writer.queue_change(rid, deleted=True, base_revision=1)
        writer.push_pending()
        self.assertEqual(reader.pull_next()["cursor"], 2)
        self.assertTrue(reader.history(rid)[-1]["deleted"])
        newcomer = self.client("frame-corrupt")
        self.server.log[0]["ciphertext_b64"] = base64.b64encode(b"plain").decode("ascii")
        with self.assertRaises(SyncError):
            newcomer.pull_next()
        self.assertEqual(newcomer.status()["cursor"], 0)


if __name__ == "__main__":
    unittest.main()
