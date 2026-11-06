"""Selector explícito de almacén. El prototipo legacy conserva el arranque previo."""
from __future__ import annotations

from pathlib import Path

from .core import SmartUniService
from .domain import DEFAULT_ANNOUNCEMENTS, DEFAULT_COURSES
from .migration import migrate_json
from .repository import JsonRepository
from .secure_storage import EncryptedSQLiteRepository, KeyStore, StorageError


def open_service(data_path: str | Path, *, mode: str = "legacy",
                 key_store: KeyStore | None = None) -> SmartUniService:
    legacy = Path(data_path).expanduser()
    if mode == "legacy":
        return SmartUniService(legacy)
    if mode != "secure":
        raise StorageError("SMARTUNI_STORAGE debe ser 'legacy' o 'secure'.")
    db_path = legacy.with_suffix(".sqlcipher")
    initial = {
        "version": 1,
        "students": [],
        "courses": DEFAULT_COURSES,
        "announcements": DEFAULT_ANNOUNCEMENTS,
    }
    if db_path.exists():
        repo = EncryptedSQLiteRepository(db_path, initial, key_store=key_store)
    elif legacy.is_file():
        # Preservamos el origen JSON para permitir una restauración verificada.
        repo = migrate_json(legacy, db_path, key_store=key_store)
    else:
        repo = EncryptedSQLiteRepository(db_path, initial, key_store=key_store)
    return SmartUniService(db_path, repository=repo)
