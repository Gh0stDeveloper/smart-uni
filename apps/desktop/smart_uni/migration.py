"""Migración sin destrucción de origen, backups SQLCipher y restauración comprobada.

Solo datos JSON v1. El origen se conserva siempre; los materiales externos NO se
migran ni se cifran aún. Los backups son bases SQLCipher, nunca JSON exportado.
"""
from __future__ import annotations

import hashlib
import json
import os
import shutil
import tempfile
import uuid
from contextlib import closing
from pathlib import Path
from typing import Callable

from .secure_storage import (
    EncryptedSQLiteRepository, KeyStore, StorageError, validate_snapshot,
)


def _sha256(path: Path) -> str:
    dig = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            dig.update(chunk)
    return dig.hexdigest()


def _fsync_dir(path: Path):
    if os.name == "posix":
        descriptor = os.open(path, os.O_RDONLY)
        try:
            os.fsync(descriptor)
        finally:
            os.close(descriptor)


def _validate_encrypted_copy(repo: EncryptedSQLiteRepository, path: Path):
    with closing(repo._driver.connect(str(path), isolation_level=None)) as con:
        con.execute("PRAGMA key = \"x'" + repo._key.hex() + "'\"")
        result = con.execute("PRAGMA integrity_check").fetchone()
        if not result or result[0] != "ok":
            raise StorageError("Copia cifrada inválida o corrupta.")
        row = con.execute("SELECT document FROM snapshot WHERE id=1").fetchone()
        if not row:
            raise StorageError("Copia sin snapshot.")
        validate_snapshot(json.loads(row[0]))
    if path.read_bytes()[:16] == b"SQLite format 3\x00":
        raise StorageError("Copia no está cifrada.")


def migrate_json(
    source: str | Path,
    destination: str | Path,
    *,
    key_store: KeyStore,
    on_step: Callable[[str], None] | None = None,
) -> EncryptedSQLiteRepository:
    """Migración staging + rename, con origen intacto y reintento seguro."""
    source, target = Path(source), Path(destination)
    if source.is_symlink() or not source.is_file() or source.stat().st_size > 20 * 1024 * 1024:
        raise StorageError("El JSON de origen no existe, es simbólico o excede 20 MiB.")
    if target.exists() or target.is_symlink():
        raise StorageError("Destino ya existe. Nunca sobreescribir una base existente.")
    original_sha = _sha256(source)
    data = json.loads(source.read_text(encoding="utf-8"))
    validate_snapshot(data)
    target.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    staging = target.with_name("." + target.name + "." + uuid.uuid4().hex + ".staging")
    try:
        stage = EncryptedSQLiteRepository(
            staging, data, key_store=key_store, identity_path=target,
        )
        with closing(stage._connection()) as con:
            con.execute("BEGIN IMMEDIATE")
            try:
                con.execute(
                    "INSERT OR REPLACE INTO metadata (key,value) VALUES (?,?)",
                    ("legacy_sha256", original_sha),
                )
                con.execute("COMMIT")
            except Exception:
                con.execute("ROLLBACK")
                raise
        stage.integrity_check()
        if on_step:
            on_step("staged")
        if _sha256(source) != original_sha:
            raise StorageError("El JSON cambió durante la migración; reintentar.")
        _validate_encrypted_copy(stage, staging)
        os.replace(staging, target)
        _fsync_dir(target.parent)
        if on_step:
            on_step("promoted")
        return EncryptedSQLiteRepository(target, data, key_store=key_store)
    finally:
        staging.unlink(missing_ok=True)


def create_backup(repo: EncryptedSQLiteRepository, destination: str | Path) -> str:
    """Respaldo cifrado consistente con writers bloqueados, no crea texto claro."""
    dest = Path(destination)
    dest.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    if dest.exists() or dest.is_symlink() or dest.resolve() == repo.path:
        raise StorageError("No sobrescribir backups ni la base original.")
    fd, tmp_name = tempfile.mkstemp(prefix=".smartuni-backup-", dir=dest.parent)
    temp = Path(tmp_name)
    try:
        with closing(repo._connection()) as con:
            con.execute("BEGIN IMMEDIATE")
            try:
                with os.fdopen(fd, "wb") as out, repo.path.open("rb") as source:
                    shutil.copyfileobj(source, out)
                    out.flush()
                    os.fsync(out.fileno())
            finally:
                con.execute("ROLLBACK")
        _validate_encrypted_copy(repo, temp)
        os.replace(temp, dest)
        _fsync_dir(dest.parent)
        return _sha256(dest)
    finally:
        temp.unlink(missing_ok=True)


def restore_backup(
    repo: EncryptedSQLiteRepository,
    backup: str | Path,
    *,
    on_step: Callable[[str], None] | None = None,
) -> Path:
    """Restaura verificando primero y guarda la base anterior (también cifrada).

    El llamador debe cerrar otras conexiones del producto antes de restaurar.
    No realiza recuperaciones automáticas ni reemplazos silenciosos.
    """
    source = Path(backup)
    if source.is_symlink() or not source.is_file() or source.resolve() == repo.path:
        raise StorageError("Respaldo inexistente o ruta inválida.")
    _validate_encrypted_copy(repo, source)
    replacement = repo.path.with_name("." + repo.path.name + "." + uuid.uuid4().hex + ".restore")
    previous = repo.path.with_name(repo.path.name + ".pre-restore-" + uuid.uuid4().hex + ".sqlcipher")
    try:
        shutil.copyfile(source, replacement)
        _validate_encrypted_copy(repo, replacement)
        if on_step:
            on_step("verified")
        if repo.path.exists():
            shutil.copyfile(repo.path, previous)
            if os.name == "posix":
                os.chmod(previous, 0o600)
        os.replace(replacement, repo.path)
        _fsync_dir(repo.path.parent)
        return previous
    finally:
        replacement.unlink(missing_ok=True)
