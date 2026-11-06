"""Cola local offline: snapshot y mensaje se confirman en UNA transacción.

Sin backend ni confirmación remota. No usar actor_ref para autorización.
"""
from __future__ import annotations

import copy
import json
import re
import uuid
from contextlib import closing
from datetime import datetime, timezone

from .domain import validate_email
from .secure_storage import EncryptedSQLiteRepository, StorageError, validate_snapshot

CONTRACT_VERSION = "1.0.0"
OPERATIONS = frozenset({
    "notes.create", "notes.update", "notes.delete", "tasks.create",
    "tasks.toggle", "events.create", "friends.add",
    "materials.import", "materials.delete", "profile.update",
})


def make_message(operation: str, actor_ref: str, payload: dict, *,
                 operation_id: str | None = None, entity_id: str | None = None) -> dict:
    """Construye un mensaje v1 para almacenar localmente; actor no autenticado."""
    message = {
        "schema_version": CONTRACT_VERSION,
        "operation": operation,
        "operation_id": operation_id or uuid.uuid4().hex,
        "actor_ref": validate_email(actor_ref),
        "occurred_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "payload": payload,
    }
    if entity_id is not None:
        message["entity_id"] = entity_id
    validate_message(message)
    return message


def validate_message(message: dict) -> bytes:
    if not isinstance(message, dict):
        raise StorageError("Mensaje de outbox inválido.")
    required = {"schema_version", "operation", "operation_id", "actor_ref", "occurred_at", "payload"}
    if not required.issubset(message) or set(message) - required - {"entity_id", "base_revision"}:
        raise StorageError("Campos de contrato desconocidos o incompletos.")
    if message["schema_version"] != CONTRACT_VERSION or message["operation"] not in OPERATIONS:
        raise StorageError("Versión/operación de contrato no compatible.")
    if not isinstance(message["operation_id"], str) or not re.fullmatch(r"[0-9a-f]{32}", message["operation_id"]):
        raise StorageError("ID de operación inválido.")
    if "entity_id" in message and (
        not isinstance(message["entity_id"], str) or not re.fullmatch(r"[0-9a-f]{32}", message["entity_id"])
    ):
        raise StorageError("ID de entidad inválido.")
    if "base_revision" in message and (
        type(message["base_revision"]) is not int or message["base_revision"] < 0
    ):
        raise StorageError("Revisión base inválida.")
    if not isinstance(message["actor_ref"], str) or validate_email(message["actor_ref"]) != message["actor_ref"]:
        raise StorageError("Referencia de actor no normalizada.")
    if not isinstance(message["occurred_at"], str):
        raise StorageError("Marca temporal inválida.")
    try:
        when = datetime.fromisoformat(message["occurred_at"].replace("Z", "+00:00"))
        if when.tzinfo is None or when.utcoffset() is None:
            raise ValueError("timestamp sin zona")
    except ValueError as exc:
        raise StorageError("Marca temporal inválida.") from exc
    if not isinstance(message["payload"], dict):
        raise StorageError("Carga de operación inválida.")
    try:
        serialized = json.dumps(message, ensure_ascii=False, allow_nan=False, separators=(",", ":")).encode("utf-8")
    except (ValueError, TypeError) as exc:
        raise StorageError("Operación no serializable.") from exc
    if len(serialized) > 1024 * 1024:
        raise StorageError("Operación excede 1 MiB.")
    return serialized


class OfflineOutbox:
    """Cola local persistente sobre un repositorio SQLCipher verificado."""

    def __init__(self, repository: EncryptedSQLiteRepository):
        if not isinstance(repository, EncryptedSQLiteRepository):
            raise StorageError("La cola solo admite SQLCipher, nunca JSON ni SQLite sin cifrar.")
        self.repo = repository

    def apply(self, message: dict, change, *, failpoint=None):
        """Ejecuta cambio(snapshot)->resultado e inserta operación atómicamente.

        Devuelve (insertado, resultado). Repetir ID no duplica la modificación.
        Las excepciones provocan ROLLBACK de ambas escrituras.
        """
        encoded = validate_message(message)
        with closing(self.repo._connection()) as con:
            con.execute("BEGIN IMMEDIATE")
            try:
                if con.execute("SELECT 1 FROM outbox WHERE operation_id=?",
                               (message["operation_id"],)).fetchone():
                    con.execute("ROLLBACK")
                    return False, None
                row = con.execute("SELECT document FROM snapshot WHERE id=1").fetchone()
                if not row:
                    raise StorageError("Snapshot de datos no existe.")
                snapshot = json.loads(row[0])
                validate_snapshot(snapshot)
                result = change(snapshot)
                validate_snapshot(snapshot)
                con.execute("UPDATE snapshot SET document=? WHERE id=1",
                            (json.dumps(snapshot, ensure_ascii=False, allow_nan=False),))
                if failpoint:
                    failpoint("after_snapshot")
                con.execute(
                    "INSERT INTO outbox (operation_id,operation_type,message,state) VALUES (?,?,?,'pending')",
                    (message["operation_id"], message["operation"], encoded.decode("utf-8")),
                )
                if failpoint:
                    failpoint("after_outbox")
                con.execute("COMMIT")
                return True, result
            except Exception:
                con.execute("ROLLBACK")
                raise

    def pending(self, limit=100) -> list[dict]:
        if type(limit) is not int or not 1 <= limit <= 1000:
            raise StorageError("Límite de outbox inválido.")
        with closing(self.repo._connection()) as con:
            rows = con.execute(
                "SELECT seq, message, state, attempts FROM outbox "
                "WHERE state IN ('pending','error') ORDER BY seq LIMIT ?",
                (limit,),
            ).fetchall()
        return [
            {"sequence": seq, "operation": json.loads(message), "state": state, "attempts": attempts}
            for seq, message, state, attempts in rows
        ]

    def mark_failed(self, operation_id: str) -> bool:
        with closing(self.repo._connection()) as con:
            con.execute("BEGIN IMMEDIATE")
            try:
                cur = con.execute(
                    "UPDATE outbox SET state='error', attempts=attempts+1 "
                    "WHERE operation_id=? AND state='pending'", (operation_id,),
                )
                con.execute("COMMIT")
                return cur.rowcount == 1
            except Exception:
                con.execute("ROLLBACK")
                raise

    def retry(self, operation_id: str) -> bool:
        with closing(self.repo._connection()) as con:
            con.execute("BEGIN IMMEDIATE")
            try:
                cur = con.execute("UPDATE outbox SET state='pending' "
                                  "WHERE operation_id=? AND state='error'", (operation_id,))
                con.execute("COMMIT")
                return cur.rowcount == 1
            except Exception:
                con.execute("ROLLBACK")
                raise

    def status(self) -> dict:
        """Estados locales discretos; nunca afirmar 'sincronizado' sin servidor."""
        with closing(self.repo._connection()) as con:
            rows = dict(con.execute("SELECT state, COUNT(*) FROM outbox GROUP BY state").fetchall())
        pending, errors = rows.get("pending", 0), rows.get("error", 0)
        return {
            "label": "Error" if errors else ("Pendiente" if pending else "Sin conexión"),
            "pending": pending,
            "errors": errors,
            "remote_confirmed": False,
        }
