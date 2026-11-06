"""End-to-end ciphertext-only incremental synchronization (experimental stage 7).

All authorization is provided by the existing OIDC dependency and database
owner_id. No endpoint accepts caller-supplied owner, plaintext, keys or roles.
The server validates SUAEAD01 framing/AAD but CANNOT validate the GCM tag,
because the key never reaches the server; clients must decrypt/authenticate.
"""
from __future__ import annotations

import base64
import hashlib
import json
import math
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, Header, HTTPException, Query, Request
from fastapi.responses import JSONResponse, Response
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select, text
from sqlalchemy.dialects.postgresql import insert as pg_insert

from .sync_models import (
    SyncBlob, SyncBlobPart, SyncConflict, SyncOwnerState, SyncResource, SyncVersion,
)

CHUNK_SIZE = 128 * 1024
MAX_BLOB_BYTES = 8 * 1024 * 1024 + 300
MAX_RECORD_BYTES = 128 * 1024
MAX_INCOMPLETE_BLOBS = 16


def rejected(detail: str, status: int = 422):
    raise HTTPException(status_code=status, detail=detail)


def decoded(value: str, maximum: int) -> bytes:
    if len(value) > (maximum + 2) // 3 * 4 + 4:
        rejected("El sobre cifrado excede el límite")
    try:
        raw = base64.b64decode(value, validate=True)
    except (ValueError, base64.binascii.Error):
        rejected("base64 inválido")
    if len(raw) > maximum or base64.b64encode(raw).decode("ascii") != value:
        rejected("Sobre cifrado no canónico")
    return raw


def expected_context(owner: UUID, resource: UUID, epoch: int) -> bytes:
    return f"sync/{owner.hex}/{resource.hex}/epoch-{epoch}".encode("ascii")


def assert_frame(ciphertext: bytes, owner: UUID, resource: UUID, epoch: int):
    """Only validates authenticated-frame structure; clients validate AEAD tag."""
    if not 1 <= epoch <= 2**31 - 1:
        rejected("Época no admitida")
    expected = expected_context(owner, resource, epoch)
    if len(ciphertext) < 23 + len(expected) + 16 or ciphertext[:8] != b"SUAEAD01":
        rejected("Formato cifrado no admitido")
    if ciphertext[8] != 1:
        rejected("Versión de cifrado no admitida")
    context_len = int.from_bytes(ciphertext[9:11], "big")
    if context_len != len(expected) or ciphertext[23:23 + context_len] != expected:
        rejected("Contexto cifrado no coincide con propietario y recurso")


def hash_request(command: dict) -> str:
    return hashlib.sha256(json.dumps(command, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def owner_lock(db, owner_id: UUID):
    """Serialize all writes to an owner to produce monotonic cursors and CAS."""
    lock = int.from_bytes(hashlib.sha256(owner_id.bytes).digest()[:8], "big", signed=True)
    db.execute(text("SELECT pg_advisory_xact_lock(:lock_id)"), {"lock_id": lock})
    db.execute(pg_insert(SyncOwnerState).values(owner_id=owner_id, cursor=0)
               .on_conflict_do_nothing(index_elements=["owner_id"]))
    return db.get(SyncOwnerState, owner_id, with_for_update=True)


class ChangeWrite(BaseModel):
    model_config = ConfigDict(extra="forbid")
    operation_id: UUID
    resource_id: UUID
    base_revision: int = Field(ge=0, le=2**63 - 2)
    epoch: int = Field(ge=1, le=2**31 - 1)
    deleted: bool = False
    ciphertext_b64: str | None = Field(default=None, max_length=180000)
    blob_id: UUID | None = None
    resolve_conflict_id: UUID | None = None


class BlobInit(BaseModel):
    model_config = ConfigDict(extra="forbid")
    blob_id: UUID
    resource_id: UUID
    epoch: int = Field(ge=1, le=2**31 - 1)
    total_size: int = Field(ge=39, le=MAX_BLOB_BYTES)
    sha256: str = Field(pattern=r"^[0-9a-f]{64}$")


def serialize_version(item: SyncVersion):
    return {
        "operation_id": str(item.operation_id),
        "resource_id": str(item.resource_id),
        "revision": item.revision,
        "cursor": item.cursor,
        "epoch": item.epoch,
        "deleted": item.deleted,
        "ciphertext_b64": base64.b64encode(item.ciphertext).decode("ascii") if item.ciphertext is not None else None,
        "blob_id": str(item.blob_id) if item.blob_id else None,
    }


def make_sync_router(authenticated, get_session):
    router = APIRouter(prefix="/api/v1/sync", tags=["encrypted-sync"])

    @router.post("/push")
    def push(data: ChangeWrite, owner=Depends(authenticated), db=Depends(get_session)):
        if data.deleted:
            if data.ciphertext_b64 is not None or data.blob_id is not None:
                rejected("El tombstone no lleva datos cifrados ni adjunto")
            payload = None
        else:
            if data.ciphertext_b64 is None:
                rejected("El cambio requiere contenedor cifrado")
            payload = decoded(data.ciphertext_b64, MAX_RECORD_BYTES)
            assert_frame(payload, owner.id, data.resource_id, data.epoch)
        digest = hash_request({
            "operation_id": data.operation_id.hex,
            "resource_id": data.resource_id.hex,
            "base_revision": data.base_revision,
            "epoch": data.epoch,
            "deleted": data.deleted,
            "ciphertext_sha256": hashlib.sha256(payload).hexdigest() if payload is not None else None,
            "blob_id": data.blob_id.hex if data.blob_id else None,
            "resolve_conflict_id": data.resolve_conflict_id.hex if data.resolve_conflict_id else None,
        })
        try:
            cursor_state = owner_lock(db, owner.id)
            existing = db.scalar(select(SyncVersion).where(
                SyncVersion.owner_id == owner.id, SyncVersion.operation_id == data.operation_id
            ))
            if existing is not None:
                if existing.request_hash != digest:
                    rejected("operation_id reutilizado con contenido distinto", 409)
                db.commit()
                return {"status": "ack", "operation_id": str(existing.operation_id),
                        "resource_id": str(existing.resource_id), "revision": existing.revision,
                        "cursor": existing.cursor, "duplicate": True}
            previous_conflict = db.scalar(select(SyncConflict).where(
                SyncConflict.owner_id == owner.id, SyncConflict.operation_id == data.operation_id
            ))
            if previous_conflict is not None:
                if previous_conflict.request_hash != digest:
                    rejected("operation_id reutilizado con contenido distinto", 409)
                answer = {"status": "conflict", "conflict_id": str(previous_conflict.id),
                          "server_revision": previous_conflict.server_revision,
                          "operation_id": str(previous_conflict.operation_id)}
                db.commit()
                return JSONResponse(status_code=409, content=answer)

            if data.blob_id is not None:
                blob = db.get(SyncBlob, data.blob_id)
                if blob is None or blob.owner_id != owner.id or not blob.complete or (
                    blob.resource_id != data.resource_id or blob.epoch != data.epoch
                ):
                    rejected("Adjunto no verificado o ajeno", 409)

            resource = db.get(SyncResource, (owner.id, data.resource_id))
            revision = resource.revision if resource is not None else 0
            if data.resolve_conflict_id is not None:
                pending = db.get(SyncConflict, data.resolve_conflict_id)
                if (pending is None or pending.owner_id != owner.id or pending.resolved
                    or pending.resource_id != data.resource_id):
                    rejected("Conflicto no disponible", 409)
            if revision != data.base_revision:
                conflict = SyncConflict(
                    id=uuid4(), owner_id=owner.id, resource_id=data.resource_id,
                    operation_id=data.operation_id, request_hash=digest,
                    base_revision=data.base_revision, server_revision=revision,
                    epoch=data.epoch, deleted=data.deleted, ciphertext=payload,
                    resolved=False,
                )
                db.add(conflict)
                db.commit()
                return JSONResponse(status_code=409, content={
                    "status": "conflict", "conflict_id": str(conflict.id),
                    "server_revision": revision, "operation_id": str(data.operation_id),
                })

            new_revision = revision + 1
            cursor_state.cursor += 1
            if resource is None:
                db.add(SyncResource(owner_id=owner.id, resource_id=data.resource_id,
                                    revision=new_revision, deleted=data.deleted))
            else:
                resource.revision = new_revision
                resource.deleted = data.deleted
            db.add(SyncVersion(
                id=uuid4(), owner_id=owner.id, resource_id=data.resource_id,
                operation_id=data.operation_id, request_hash=digest,
                cursor=cursor_state.cursor, revision=new_revision, epoch=data.epoch,
                deleted=data.deleted, ciphertext=payload, blob_id=data.blob_id,
            ))
            if data.resolve_conflict_id is not None:
                pending.resolved = True
            answer = {"status": "ack", "operation_id": str(data.operation_id),
                      "resource_id": str(data.resource_id), "revision": new_revision,
                      "cursor": cursor_state.cursor, "duplicate": False}
            db.commit()
            return answer
        except Exception:
            db.rollback()
            raise

    @router.get("/pull")
    def pull(cursor: int = Query(default=0, ge=0),
             limit: int = Query(default=30, ge=1, le=100),
             owner=Depends(authenticated), db=Depends(get_session)):
        changes = db.scalars(
            select(SyncVersion).where(SyncVersion.owner_id == owner.id,
                                      SyncVersion.cursor > cursor)
            .order_by(SyncVersion.cursor).limit(limit + 1)
        ).all()
        more = len(changes) > limit
        page = changes[:limit]
        state = db.get(SyncOwnerState, owner.id)
        return {
            "cursor": page[-1].cursor if page else cursor,
            "has_more": more,
            "high_watermark": state.cursor if state else 0,
            "changes": [serialize_version(row) for row in page],
        }

    @router.get("/conflicts")
    def conflicts(owner=Depends(authenticated), db=Depends(get_session)):
        rows = db.scalars(
            select(SyncConflict).where(SyncConflict.owner_id == owner.id,
                                      SyncConflict.resolved.is_(False))
            .order_by(SyncConflict.created_at, SyncConflict.id).limit(100)
        ).all()
        return [{
            "conflict_id": str(item.id),
            "operation_id": str(item.operation_id),
            "resource_id": str(item.resource_id),
            "base_revision": item.base_revision,
            "server_revision_at_detection": item.server_revision,
            "epoch": item.epoch, "deleted": item.deleted,
            "ciphertext_b64": base64.b64encode(item.ciphertext).decode("ascii") if item.ciphertext is not None else None,
        } for item in rows]

    @router.post("/conflicts/{conflict_id}/dismiss")
    def dismiss(conflict_id: UUID, owner=Depends(authenticated), db=Depends(get_session)):
        try:
            owner_lock(db, owner.id)
            item = db.get(SyncConflict, conflict_id)
            if item is None or item.owner_id != owner.id:
                rejected("Conflicto no encontrado", 404)
            item.resolved = True
            db.commit()
            return {"status": "dismissed"}
        except Exception:
            db.rollback()
            raise

    @router.post("/blobs/init")
    def init_blob(data: BlobInit, owner=Depends(authenticated), db=Depends(get_session)):
        try:
            owner_lock(db, owner.id)
            item = db.get(SyncBlob, data.blob_id)
            if item is None:
                incompletes = db.scalars(select(SyncBlob.id).where(
                    SyncBlob.owner_id == owner.id, SyncBlob.complete.is_(False)
                )).all()
                if len(incompletes) >= MAX_INCOMPLETE_BLOBS:
                    rejected("Demasiados archivos pendientes", 429)
                item = SyncBlob(
                    id=data.blob_id, owner_id=owner.id, resource_id=data.resource_id,
                    epoch=data.epoch, total_size=data.total_size, sha256=data.sha256, complete=False,
                )
                db.add(item)
                db.flush()
            elif (item.owner_id != owner.id or item.resource_id != data.resource_id
                  or item.epoch != data.epoch or item.total_size != data.total_size
                  or item.sha256 != data.sha256):
                rejected("Identificador de adjunto en uso o ajeno", 409)
            indices = db.scalars(select(SyncBlobPart.part_index).where(
                SyncBlobPart.blob_id == item.id
            ).order_by(SyncBlobPart.part_index)).all()
            answer = {
                "blob_id": str(item.id), "chunk_size": CHUNK_SIZE,
                "received_parts": indices, "complete": item.complete,
            }
            db.commit()
            return answer
        except Exception:
            db.rollback()
            raise

    @router.put("/blobs/{blob_id}/parts/{index}")
    async def send_part(blob_id: UUID, index: int, request: Request,
                        x_chunk_sha256: str = Header(),
                        owner=Depends(authenticated), db=Depends(get_session)):
        if not 0 <= index < 65 or len(x_chunk_sha256) != 64 or any(c not in "0123456789abcdef" for c in x_chunk_sha256):
            rejected("Índice o checksum inválido")
        chunks = []
        size = 0
        async for portion in request.stream():
            size += len(portion)
            if size > CHUNK_SIZE:
                rejected("Fragmento excede 128 KiB", 413)
            chunks.append(portion)
        raw = b"".join(chunks)
        if hashlib.sha256(raw).hexdigest() != x_chunk_sha256:
            rejected("Checksum del fragmento inválido", 422)
        try:
            owner_lock(db, owner.id)
            blob = db.get(SyncBlob, blob_id, with_for_update=True)
            if blob is None or blob.owner_id != owner.id:
                rejected("Adjunto no encontrado", 404)
            total_parts = math.ceil(blob.total_size / CHUNK_SIZE)
            if index >= total_parts:
                rejected("Fragmento fuera de rango", 422)
            expected = min(CHUNK_SIZE, blob.total_size - index * CHUNK_SIZE)
            if len(raw) != expected:
                rejected("Longitud de fragmento no coincide", 422)
            previous = db.get(SyncBlobPart, (blob_id, index))
            if previous is not None:
                if previous.sha256 != x_chunk_sha256 or previous.data != raw:
                    rejected("Fragmento ya existe con bytes distintos", 409)
                db.commit()
                return {"status": "stored", "duplicate": True, "part_index": index}
            if blob.complete:
                rejected("Adjunto completado, sin nuevas partes", 409)
            db.add(SyncBlobPart(blob_id=blob_id, part_index=index, sha256=x_chunk_sha256, data=raw))
            db.commit()
            return {"status": "stored", "duplicate": False, "part_index": index}
        except Exception:
            db.rollback()
            raise

    @router.post("/blobs/{blob_id}/complete")
    def complete(blob_id: UUID, owner=Depends(authenticated), db=Depends(get_session)):
        try:
            owner_lock(db, owner.id)
            blob = db.get(SyncBlob, blob_id, with_for_update=True)
            if blob is None or blob.owner_id != owner.id:
                rejected("Adjunto no encontrado", 404)
            if blob.complete:
                db.commit()
                return {"status": "complete", "sha256": blob.sha256}
            parts = db.scalars(select(SyncBlobPart).where(
                SyncBlobPart.blob_id == blob.id
            ).order_by(SyncBlobPart.part_index)).all()
            expected_count = math.ceil(blob.total_size / CHUNK_SIZE)
            if [p.part_index for p in parts] != list(range(expected_count)):
                rejected("Faltan fragmentos", 409)
            content = b"".join(part.data for part in parts)
            if len(content) != blob.total_size or hashlib.sha256(content).hexdigest() != blob.sha256:
                rejected("Checksum final inválido", 422)
            assert_frame(content, owner.id, blob.resource_id, blob.epoch)
            blob.complete = True
            db.commit()
            return {"status": "complete", "sha256": blob.sha256}
        except Exception:
            db.rollback()
            raise

    @router.get("/blobs/{blob_id}/parts/{index}")
    def get_part(blob_id: UUID, index: int, owner=Depends(authenticated), db=Depends(get_session)):
        blob = db.get(SyncBlob, blob_id)
        if blob is None or blob.owner_id != owner.id or not blob.complete:
            rejected("Adjunto no encontrado", 404)
        part = db.get(SyncBlobPart, (blob_id, index))
        if part is None:
            rejected("Fragmento no encontrado", 404)
        return Response(part.data, media_type="application/octet-stream", headers={
            "X-Chunk-Sha256": part.sha256, "Cache-Control": "no-store",
        })

    @router.get("/blobs/{blob_id}")
    def get_blob(blob_id: UUID, owner=Depends(authenticated), db=Depends(get_session)):
        blob = db.get(SyncBlob, blob_id)
        if blob is None or blob.owner_id != owner.id or not blob.complete:
            rejected("Adjunto no encontrado", 404)
        parts = db.scalars(select(SyncBlobPart).where(
            SyncBlobPart.blob_id == blob_id
        ).order_by(SyncBlobPart.part_index)).all()
        content = b"".join(part.data for part in parts)
        if len(content) != blob.total_size or hashlib.sha256(content).hexdigest() != blob.sha256:
            rejected("Adjunto corrupto", 503)
        return Response(content, media_type="application/octet-stream", headers={
            "X-Content-Sha256": blob.sha256, "Cache-Control": "no-store",
        })

    return router
