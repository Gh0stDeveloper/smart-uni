"""Opt-in encrypted SQLCipher sync client; never sends plaintext v1 outbox.

Authentication (OIDC bearer), owner UUID and 32-byte content key must be
provisioned by an authorized session. The existing desktop UI does not yet
have that identity flow. Production crypto always calls the Rust C ABI.
"""
from __future__ import annotations

import base64
import hashlib
import math
import secrets
import time
from contextlib import closing
from urllib.parse import urlsplit
from uuid import UUID, uuid4

from .secure_crypto import ContentCrypto
from .secure_storage import EncryptedSQLiteRepository, StorageError

PART = 128 * 1024
MAX_BLOB = 8 * 1024 * 1024 + 300


class SyncError(StorageError):
    pass


class SyncAuthError(SyncError):
    pass


def uuid(value):
    return value if isinstance(value, UUID) else UUID(str(value))


def b64_decode(value):
    try:
        raw = base64.b64decode(value, validate=True)
        if base64.b64encode(raw).decode("ascii") != value:
            raise ValueError("noncanonical")
        return raw
    except (ValueError, TypeError, base64.binascii.Error) as exc:
        raise SyncError("Datos cifrados no canónicos") from exc


class EncryptedSyncClient:
    """Explicit authenticated sync; ciphertext never falls back to plaintext."""

    def __init__(self, repository: EncryptedSQLiteRepository, owner_id, content_key: bytes,
                 transport, bearer_supplier, *, crypto=None, clock=None, allow_test_transport=False):
        if not isinstance(repository, EncryptedSQLiteRepository):
            raise SyncError("Solo SQLCipher admite sincronización cifrada")
        self.repo = repository
        self.owner_id = uuid(owner_id)
        if not isinstance(content_key, bytes) or len(content_key) != 32:
            raise SyncError("Se exige clave de contenido aprovisionada de 32 bytes")
        if not callable(bearer_supplier):
            raise SyncAuthError("Falta proveedor de sesión OIDC")
        if not allow_test_transport:
            base = getattr(transport, "base_url", None)
            if base is None or urlsplit(str(base)).scheme != "https":
                raise SyncError("Se exige HTTPS para sincronización remota")
        self.key = content_key
        self.crypto = crypto if crypto is not None else ContentCrypto()
        self.transport = transport
        self.bearer_supplier = bearer_supplier
        self.clock = clock if clock is not None else time.time
        self.verified = False
        self._schema()

    def _schema(self):
        with closing(self.repo._connection()) as con:
            con.execute("BEGIN IMMEDIATE")
            try:
                ddl = (
                    "CREATE TABLE IF NOT EXISTS encrypted_sync_owner ("
                    "id INTEGER PRIMARY KEY CHECK(id=1), owner TEXT NOT NULL)",
                    "CREATE TABLE IF NOT EXISTS encrypted_sync_meta ("
                    "id INTEGER PRIMARY KEY CHECK(id=1), cursor INTEGER NOT NULL)",
                    "CREATE TABLE IF NOT EXISTS encrypted_sync_queue ("
                    "operation_id TEXT PRIMARY KEY, resource_id TEXT NOT NULL,"
                    "base_revision INTEGER NOT NULL, epoch INTEGER NOT NULL, deleted INTEGER NOT NULL,"
                    "ciphertext BLOB NOT NULL, blob_id TEXT, resolve_conflict_id TEXT,"
                    "state TEXT NOT NULL CHECK(state IN ('pending','conflict','acked','resolved','dismissed','error')),"
                    "attempts INTEGER NOT NULL DEFAULT 0, next_attempt REAL NOT NULL DEFAULT 0,"
                    "conflict_id TEXT, server_revision INTEGER, ack_cursor INTEGER)",
                    "CREATE TABLE IF NOT EXISTS encrypted_sync_inbox ("
                    "cursor INTEGER PRIMARY KEY, operation_id TEXT NOT NULL UNIQUE,"
                    "resource_id TEXT NOT NULL, revision INTEGER NOT NULL, epoch INTEGER NOT NULL,"
                    "deleted INTEGER NOT NULL, ciphertext BLOB NOT NULL, blob_id TEXT)",
                    "CREATE TABLE IF NOT EXISTS encrypted_sync_uploads ("
                    "blob_id TEXT PRIMARY KEY, resource_id TEXT NOT NULL, base_revision INTEGER NOT NULL,"
                    "epoch INTEGER NOT NULL, ciphertext BLOB NOT NULL, sha256 TEXT NOT NULL,"
                    "state TEXT NOT NULL CHECK(state IN ('pending','complete')))",
                    "CREATE TABLE IF NOT EXISTS encrypted_sync_downloads ("
                    "blob_id TEXT PRIMARY KEY, resource_id TEXT NOT NULL, base_revision INTEGER NOT NULL,"
                    "epoch INTEGER NOT NULL, total_size INTEGER NOT NULL, sha256 TEXT NOT NULL)",
                    "CREATE TABLE IF NOT EXISTS encrypted_sync_download_parts ("
                    "blob_id TEXT NOT NULL, part_index INTEGER NOT NULL, data BLOB NOT NULL,"
                    "PRIMARY KEY(blob_id,part_index))",
                )
                for statement in ddl:
                    con.execute(statement)
                con.execute("INSERT OR IGNORE INTO encrypted_sync_owner VALUES (1,?)",
                            (str(self.owner_id),))
                actual = con.execute("SELECT owner FROM encrypted_sync_owner WHERE id=1").fetchone()[0]
                if actual != str(self.owner_id):
                    raise SyncAuthError("La base pertenece a otra identidad")
                con.execute("INSERT OR IGNORE INTO encrypted_sync_meta VALUES (1,0)")
                con.execute("COMMIT")
            except Exception:
                con.execute("ROLLBACK")
                raise

    def _auth(self):
        value = self.bearer_supplier()
        if not isinstance(value, str) or not 10 <= len(value) <= 16384:
            raise SyncAuthError("No hay sesión autenticada disponible")
        return {"Authorization": "Bearer " + value}

    def verify_identity(self):
        try:
            response = self.transport.get("/api/v1/me", headers=self._auth())
        except Exception as exc:
            raise SyncError("Identidad remota inaccesible") from exc
        if response.status_code != 200:
            raise SyncAuthError("Credenciales OIDC no aceptadas")
        try:
            actual = uuid(response.json()["id"])
        except (KeyError, ValueError, TypeError) as exc:
            raise SyncAuthError("Respuesta de identidad mal formada") from exc
        if actual != self.owner_id:
            raise SyncAuthError("La sesión remota y la identidad de esta base difieren")
        self.verified = True

    def _headers(self):
        if not self.verified:
            self.verify_identity()
        return self._auth()

    def _context(self, resource, epoch, base, kind):
        if kind not in ("put", "delete", "blob"):
            raise SyncError("Tipo de objeto cifrado no permitido")
        return (f"sync/{self.owner_id.hex}/{uuid(resource).hex}/epoch-{epoch}"
                f"/base-{base}/kind-{kind}").encode("ascii")

    def queue_change(self, resource, plaintext=b"", *, base_revision=0, epoch=1,
                     deleted=False, blob_id=None, resolve_conflict_id=None):
        resource = uuid(resource)
        if (not isinstance(plaintext, bytes) or type(base_revision) is not int
            or not 0 <= base_revision < 2**63 - 1 or type(epoch) is not int
            or not 1 <= epoch <= 2**31 - 1 or (deleted and blob_id is not None)):
            raise SyncError("Parámetros de operación inválidos")
        kind = "delete" if deleted else "put"
        encrypted = self.crypto.encrypt(
            self.key, self._context(resource, epoch, base_revision, kind),
            b"tombstone:v1" if deleted else plaintext,
        )
        if len(encrypted) > 128 * 1024:
            raise SyncError("Usa upload por fragmentos para recursos grandes")
        op = str(uuid4())
        with closing(self.repo._connection()) as con:
            con.execute(
                "INSERT INTO encrypted_sync_queue (operation_id,resource_id,base_revision,"
                "epoch,deleted,ciphertext,blob_id,resolve_conflict_id,state) "
                "VALUES (?,?,?,?,?,?,?,?, 'pending')",
                (op, str(resource), base_revision, epoch, int(deleted), encrypted,
                 str(uuid(blob_id)) if blob_id else None,
                 str(uuid(resolve_conflict_id)) if resolve_conflict_id else None),
            )
        return op

    def _queue_update(self, op, statement, *args):
        with closing(self.repo._connection()) as con:
            con.execute("BEGIN IMMEDIATE")
            try:
                con.execute(statement, (*args, op))
                con.execute("COMMIT")
            except Exception:
                con.execute("ROLLBACK")
                raise

    def _schedule_retry(self, op, count):
        delay = min(3600, 2**min(count + 1, 10)) + secrets.randbelow(1000) / 1000
        self._queue_update(
            op, "UPDATE encrypted_sync_queue SET attempts=attempts+1,next_attempt=? "
            "WHERE operation_id=? AND state='pending'", self.clock() + delay,
        )

    def push_pending(self, limit=20, *, force=False):
        if type(limit) is not int or not 1 <= limit <= 100:
            raise SyncError("Límite de cola inválido")
        with closing(self.repo._connection()) as con:
            rows = con.execute(
                "SELECT operation_id,resource_id,base_revision,epoch,deleted,ciphertext,"
                "blob_id,resolve_conflict_id,attempts FROM encrypted_sync_queue "
                "WHERE state='pending' AND (next_attempt<=? OR ?=1) ORDER BY rowid LIMIT ?",
                (self.clock(), int(force), limit),
            ).fetchall()
        results = []
        for op, rid, base, epoch, deleted, encrypted, blob, conflict, attempts in rows:
            try:
                response = self.transport.post("/api/v1/sync/push",
                    headers=self._headers(), json={
                        "operation_id": op, "resource_id": rid, "base_revision": base,
                        "epoch": epoch, "deleted": bool(deleted),
                        "ciphertext_b64": base64.b64encode(encrypted).decode("ascii"),
                        "blob_id": blob, "resolve_conflict_id": conflict,
                    })
            except SyncAuthError:
                raise
            except Exception:
                self._schedule_retry(op, attempts)
                results.append((op, "retry_scheduled"))
                break
            if response.status_code == 200:
                try:
                    answer = response.json()
                    if (answer["status"] != "ack" or uuid(answer["operation_id"]) != uuid(op)
                        or uuid(answer["resource_id"]) != uuid(rid)
                        or type(answer["revision"]) is not int or answer["revision"] != base + 1
                        or type(answer["cursor"]) is not int or answer["cursor"] <= 0):
                        raise ValueError("ACK incompatible")
                except (KeyError, TypeError, ValueError) as exc:
                    raise SyncError("ACK inválido, operación conservada") from exc
                self._queue_update(
                    op, "UPDATE encrypted_sync_queue SET state='acked',ack_cursor=?,"
                    "server_revision=? WHERE operation_id=? AND state='pending'",
                    answer["cursor"], answer["revision"],
                )
                results.append((op, "ack"))
            elif response.status_code == 409:
                try:
                    answer = response.json()
                    if answer["status"] != "conflict" or uuid(answer["operation_id"]) != uuid(op):
                        raise ValueError("conflicto mal formado")
                    uuid(answer["conflict_id"])
                    rev = answer["server_revision"]
                    if type(rev) is not int or rev < 0:
                        raise ValueError("revisión inválida")
                except (KeyError, TypeError, ValueError) as exc:
                    raise SyncError("Conflicto inválido, operación conservada") from exc
                self._queue_update(
                    op, "UPDATE encrypted_sync_queue SET state='conflict',conflict_id=?,"
                    "server_revision=? WHERE operation_id=? AND state='pending'",
                    answer["conflict_id"], rev,
                )
                results.append((op, "conflict"))
            elif response.status_code in (401, 403):
                raise SyncAuthError("Sesión caducada, cola conservada")
            elif response.status_code in (400, 413, 415, 422):
                self._queue_update(
                    op, "UPDATE encrypted_sync_queue SET state='error',attempts=attempts+1 "
                    "WHERE operation_id=? AND state='pending'",
                )
                results.append((op, "error"))
            else:
                self._schedule_retry(op, attempts)
                results.append((op, "retry_scheduled"))
                break
        return results

    def pull_next(self, limit=30, *, failpoint=None):
        if type(limit) is not int or not 1 <= limit <= 100:
            raise SyncError("Límite de pull inválido")
        with closing(self.repo._connection()) as con:
            before = con.execute("SELECT cursor FROM encrypted_sync_meta WHERE id=1").fetchone()[0]
        try:
            response = self.transport.get(f"/api/v1/sync/pull?cursor={before}&limit={limit}",
                                          headers=self._headers())
        except SyncAuthError:
            raise
        except Exception as exc:
            raise SyncError("Red no disponible; cursor conservado") from exc
        if response.status_code in (401, 403):
            raise SyncAuthError("Sesión inválida; cursor conservado")
        if response.status_code != 200:
            raise SyncError("Pull no confirmado; cursor conservado")
        result = response.json()
        changes = result.get("changes")
        if (not isinstance(changes, list) or len(changes) > limit
            or type(result.get("cursor")) is not int):
            raise SyncError("Respuesta de pull inválida")
        parsed = []
        cursor = before
        for item in changes:
            try:
                next_seq, rev, epoch = item["cursor"], item["revision"], item["epoch"]
                if (type(next_seq) is not int or next_seq != cursor + 1
                    or type(rev) is not int or rev < 1 or type(epoch) is not int
                    or epoch < 1 or type(item["deleted"]) is not bool):
                    raise ValueError("Orden o revisión inválido")
                opid, rid = uuid(item["operation_id"]), uuid(item["resource_id"])
                cipher = b64_decode(item["ciphertext_b64"])
                kind = "delete" if item["deleted"] else "put"
                plain = self.crypto.decrypt(self.key, self._context(rid, epoch, rev - 1, kind), cipher)
                if item["deleted"] and plain != b"tombstone:v1":
                    raise ValueError("Tombstone no autenticado")
                blob_id = str(uuid(item["blob_id"])) if item.get("blob_id") else None
                parsed.append((next_seq, str(opid), str(rid), rev, epoch,
                               int(item["deleted"]), cipher, blob_id))
                cursor = next_seq
            except Exception as exc:
                raise SyncError("Un cambio no se pudo autenticar; cursor preservado") from exc
        if result["cursor"] != cursor:
            raise SyncError("Cursor remoto incoherente")
        with closing(self.repo._connection()) as con:
            con.execute("BEGIN IMMEDIATE")
            try:
                current = con.execute("SELECT cursor FROM encrypted_sync_meta WHERE id=1").fetchone()[0]
                if current != before:
                    raise SyncError("Cursor modificado por otro proceso")
                for i, row in enumerate(parsed):
                    con.execute(
                        "INSERT INTO encrypted_sync_inbox "
                        "(cursor,operation_id,resource_id,revision,epoch,deleted,ciphertext,blob_id)"
                        " VALUES (?,?,?,?,?,?,?,?)", row,
                    )
                    if failpoint:
                        failpoint(i)
                con.execute("UPDATE encrypted_sync_meta SET cursor=? WHERE id=1", (cursor,))
                con.execute("COMMIT")
            except Exception:
                con.execute("ROLLBACK")
                raise
        return {"count": len(parsed), "cursor": cursor, "has_more": result.get("has_more", False)}

    def history(self, resource):
        with closing(self.repo._connection()) as con:
            rows = con.execute(
                "SELECT cursor,revision,epoch,deleted,ciphertext FROM encrypted_sync_inbox "
                "WHERE resource_id=? ORDER BY cursor", (str(uuid(resource)),),
            ).fetchall()
        versions = []
        for cursor, revision, epoch, deleted, encrypted in rows:
            kind = "delete" if deleted else "put"
            plain = self.crypto.decrypt(
                self.key, self._context(resource, epoch, revision - 1, kind), encrypted,
            )
            if deleted and plain != b"tombstone:v1":
                raise SyncError("Tombstone alterado")
            versions.append({"cursor": cursor, "revision": revision,
                             "deleted": bool(deleted),
                             "plaintext": None if deleted else plain})
        return versions

    def resolve_keep_local(self, operation_id):
        """Explicit user choice; re-encrypt candidate against newest server revision."""
        op = str(uuid(operation_id))
        with closing(self.repo._connection()) as con:
            con.execute("BEGIN IMMEDIATE")
            try:
                row = con.execute(
                    "SELECT resource_id,base_revision,epoch,deleted,ciphertext,blob_id,"
                    "conflict_id,server_revision FROM encrypted_sync_queue "
                    "WHERE operation_id=? AND state='conflict'", (op,),
                ).fetchone()
                if row is None:
                    raise SyncError("No existe conflicto abierto")
                rid, base, epoch, deleted, encrypted, blob, conflict, server_revision = row
                if blob:
                    raise SyncError("Reasignar adjunto requiere nueva carga verificada")
                kind = "delete" if deleted else "put"
                plaintext = self.crypto.decrypt(
                    self.key, self._context(rid, epoch, base, kind), encrypted,
                )
                if deleted and plaintext != b"tombstone:v1":
                    raise SyncError("Eliminación adulterada")
                fresh = self.crypto.encrypt(
                    self.key, self._context(rid, epoch, server_revision, kind), plaintext,
                )
                new_op = str(uuid4())
                con.execute(
                    "INSERT INTO encrypted_sync_queue "
                    "(operation_id,resource_id,base_revision,epoch,deleted,ciphertext,"
                    "resolve_conflict_id,state) VALUES (?,?,?,?,?,?,?,'pending')",
                    (new_op, rid, server_revision, epoch, deleted, fresh, conflict),
                )
                con.execute(
                    "UPDATE encrypted_sync_queue SET state='resolved' WHERE operation_id=?", (op,)
                )
                con.execute("COMMIT")
                return new_op
            except Exception:
                con.execute("ROLLBACK")
                raise

    def dismiss_conflict(self, operation_id):
        """Explicit user choice; preserve dismissed candidate encrypted on device."""
        op = str(uuid(operation_id))
        with closing(self.repo._connection()) as con:
            row = con.execute(
                "SELECT conflict_id FROM encrypted_sync_queue WHERE operation_id=? "
                "AND state='conflict'", (op,),
            ).fetchone()
        if row is None:
            raise SyncError("Conflicto inexistente")
        resp = self.transport.post(
            f"/api/v1/sync/conflicts/{row[0]}/dismiss", headers=self._headers(),
        )
        if resp.status_code != 200 or resp.json().get("status") != "dismissed":
            raise SyncError("Servidor no confirmó descarte")
        self._queue_update(
            op, "UPDATE encrypted_sync_queue SET state='dismissed' "
            "WHERE operation_id=? AND state='conflict'",
        )

    def stage_blob(self, resource, plaintext, *, base_revision=0, epoch=1):
        if not isinstance(plaintext, bytes) or len(plaintext) > 8 * 1024 * 1024:
            raise SyncError("Adjunto supera el límite de 8 MiB")
        rid = uuid(resource)
        encrypted = self.crypto.encrypt(
            self.key, self._context(rid, epoch, base_revision, "blob"), plaintext,
        )
        if len(encrypted) > MAX_BLOB:
            raise SyncError("Contenedor demasiado grande")
        blob_id = str(uuid4())
        with closing(self.repo._connection()) as con:
            con.execute(
                "INSERT INTO encrypted_sync_uploads "
                "(blob_id,resource_id,base_revision,epoch,ciphertext,sha256,state)"
                " VALUES (?,?,?,?,?,?,'pending')",
                (blob_id,str(rid),base_revision,epoch,encrypted,
                 hashlib.sha256(encrypted).hexdigest()),
            )
        return blob_id

    def upload_blob(self, blob_id, *, max_parts=None):
        blob_id = str(uuid(blob_id))
        with closing(self.repo._connection()) as con:
            row = con.execute(
                "SELECT resource_id,base_revision,epoch,ciphertext,sha256,state "
                "FROM encrypted_sync_uploads WHERE blob_id=?", (blob_id,),
            ).fetchone()
        if row is None:
            raise SyncError("No existe la carga local")
        rid, base, epoch, encrypted, digest, state = row
        if state == "complete":
            return {"status": "complete"}
        response = self.transport.post("/api/v1/sync/blobs/init", headers=self._headers(), json={
            "blob_id":blob_id, "resource_id":rid, "base_revision":base, "epoch":epoch,
            "total_size":len(encrypted), "sha256":digest,
        })
        if response.status_code != 200:
            raise SyncError("No se pudo inicializar el adjunto")
        manifest = response.json()
        if manifest.get("blob_id") != blob_id or manifest.get("chunk_size") != PART:
            raise SyncError("Manifest remoto no válido")
        existing = set(manifest.get("received_parts", []))
        count = math.ceil(len(encrypted) / PART)
        if any(type(i) is not int or not 0 <= i < count for i in existing):
            raise SyncError("Manifest de fragmentos inválido")
        sent = 0
        for i in range(count):
            if i in existing:
                continue
            if max_parts is not None and sent >= max_parts:
                return {"status": "partial", "sent": sent}
            chunk = encrypted[i*PART:(i+1)*PART]
            result = self.transport.put(
                f"/api/v1/sync/blobs/{blob_id}/parts/{i}",
                content=chunk, headers={
                    **self._headers(), "X-Chunk-Sha256":hashlib.sha256(chunk).hexdigest(),
                })
            if result.status_code != 200:
                raise SyncError("Carga interrumpida; ciphertext conservado en SQLCipher")
            sent += 1
        done = self.transport.post(
            f"/api/v1/sync/blobs/{blob_id}/complete", headers=self._headers(),
        )
        if done.status_code != 200 or done.json().get("sha256") != digest:
            raise SyncError("Integridad de carga no confirmada")
        with closing(self.repo._connection()) as con:
            con.execute(
                "UPDATE encrypted_sync_uploads SET state='complete' WHERE blob_id=?", (blob_id,)
            )
        return {"status": "complete", "sent": sent}

    def download_blob(self, blob_id, resource, *, base_revision=0, epoch=1):
        """Persist partial ciphertext only; authenticate before returning in-memory bytes."""
        blob_id, rid = str(uuid(blob_id)), str(uuid(resource))
        response = self.transport.get(
            f"/api/v1/sync/blobs/{blob_id}/manifest", headers=self._headers(),
        )
        if response.status_code != 200:
            raise SyncError("No se obtuvo manifest de descarga")
        meta = response.json()
        if (meta.get("blob_id") != blob_id or meta.get("resource_id") != rid
            or meta.get("base_revision") != base_revision or meta.get("epoch") != epoch
            or meta.get("chunk_size") != PART
            or type(meta.get("total_size")) is not int
            or not 1 <= meta["total_size"] <= MAX_BLOB
            or not isinstance(meta.get("sha256"), str) or len(meta["sha256"]) != 64):
            raise SyncError("Manifest incompatible con el recurso")
        expected = (rid, base_revision, epoch, meta["total_size"], meta["sha256"])
        with closing(self.repo._connection()) as con:
            con.execute("BEGIN IMMEDIATE")
            try:
                prior = con.execute(
                    "SELECT resource_id,base_revision,epoch,total_size,sha256 "
                    "FROM encrypted_sync_downloads WHERE blob_id=?", (blob_id,),
                ).fetchone()
                if prior is not None and prior != expected:
                    raise SyncError("El manifest cambió durante la descarga")
                con.execute(
                    "INSERT OR IGNORE INTO encrypted_sync_downloads VALUES (?,?,?,?,?,?)",
                    (blob_id, *expected),
                )
                con.execute("COMMIT")
            except Exception:
                con.execute("ROLLBACK")
                raise
        count = math.ceil(meta["total_size"] / PART)
        for i in range(count):
            with closing(self.repo._connection()) as con:
                previous = con.execute(
                    "SELECT data FROM encrypted_sync_download_parts "
                    "WHERE blob_id=? AND part_index=?", (blob_id, i),
                ).fetchone()
            if previous:
                continue
            part = self.transport.get(
                f"/api/v1/sync/blobs/{blob_id}/parts/{i}", headers=self._headers(),
            )
            if part.status_code != 200:
                raise SyncError("Descarga pausada; ciphertext previo conservado")
            bytes_received = part.content
            required = min(PART, meta["total_size"] - i*PART)
            if (len(bytes_received) != required or
                hashlib.sha256(bytes_received).hexdigest() != part.headers.get("X-Chunk-Sha256")):
                raise SyncError("Fragmento descargado corrupto")
            with closing(self.repo._connection()) as con:
                con.execute(
                    "INSERT OR IGNORE INTO encrypted_sync_download_parts VALUES (?,?,?)",
                    (blob_id, i, bytes_received),
                )
        with closing(self.repo._connection()) as con:
            chunks = con.execute(
                "SELECT part_index,data FROM encrypted_sync_download_parts "
                "WHERE blob_id=? ORDER BY part_index", (blob_id,),
            ).fetchall()
        if [p[0] for p in chunks] != list(range(count)):
            raise SyncError("Faltan fragmentos")
        ciphertext = b"".join(p[1] for p in chunks)
        if len(ciphertext) != meta["total_size"] or hashlib.sha256(ciphertext).hexdigest() != meta["sha256"]:
            raise SyncError("Hash final del archivo inválido")
        return self.crypto.decrypt(
            self.key, self._context(rid, epoch, base_revision, "blob"), ciphertext,
        )

    def status(self):
        with closing(self.repo._connection()) as con:
            grouped = dict(con.execute(
                "SELECT state,count(*) FROM encrypted_sync_queue GROUP BY state"
            ).fetchall())
            cursor = con.execute("SELECT cursor FROM encrypted_sync_meta WHERE id=1").fetchone()[0]
        return {
            "pending": grouped.get("pending", 0),
            "conflicts": grouped.get("conflict", 0),
            "errors": grouped.get("error", 0),
            "acked": grouped.get("acked", 0),
            "cursor": cursor,
            "remote_identity_verified": self.verified,
            "label": "Error" if grouped.get("error") else
                     "Conflicto" if grouped.get("conflict") else
                     "Pendiente" if grouped.get("pending") else "Sin conexión",
        }
