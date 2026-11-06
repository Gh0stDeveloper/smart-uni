"""Recuperación explícita de la clave SQLCipher, sin fallback plaintext.

Requiere conservar además la copia cifrada de la DB. Frase de recuperación
no se solicita en la GUI del prototipo ni se escribe en logs/disco.
"""
from __future__ import annotations

from contextlib import closing
from pathlib import Path

from .secure_crypto import ContentCrypto
from .secure_storage import (
    EncryptedSQLiteRepository, KeyStore, OSKeyStore,
    StorageError, cipher_driver, key_id,
)


def export_database_recovery(repo: EncryptedSQLiteRepository, phrase: str, *, native=None) -> bytes:
    """Devuelve 84 bytes cifrados para almacenamiento externo fuera del equipo."""
    if not isinstance(repo, EncryptedSQLiteRepository):
        raise StorageError("Solo se permite una base SQLCipher verificada.")
    repo.integrity_check()
    native = native if native is not None else ContentCrypto()
    return native.export_recovery(repo._key, phrase)


def restore_database_recovery(path: str | Path, package: bytes, phrase: str,
                              *, key_store: KeyStore | None = None, native=None) -> None:
    """Valida el backup SQLCipher ANTES de insertar la clave recuperada en OS keyring."""
    location = Path(path).expanduser()
    if location.is_symlink() or not location.is_file():
        raise StorageError("Primero restaura una base SQLCipher válida y no enlazada.")
    location = location.resolve()
    native = native if native is not None else ContentCrypto()
    recovered = native.restore_recovery(package, phrase)
    if len(recovered) != 32:
        raise StorageError("Copia de recuperación con clave inválida.")
    driver = cipher_driver()
    with closing(driver.connect(str(location), isolation_level=None, timeout=10)) as connection:
        try:
            connection.execute("PRAGMA key = \"x'" + recovered.hex() + "'\"")
            cipher_version = connection.execute("PRAGMA cipher_version").fetchone()
            if not cipher_version or not cipher_version[0]:
                raise StorageError("El driver no ofrece SQLCipher.")
            integrity = connection.execute("PRAGMA integrity_check").fetchone()
            if not integrity or integrity[0] != "ok":
                raise StorageError("La clave no abre una base SQLCipher íntegra.")
            if connection.execute("SELECT 1 FROM snapshot WHERE id=1").fetchone() is None:
                raise StorageError("Snapshot de usuario ausente.")
        except Exception as exc:
            raise StorageError("Recuperación rechazada: clave incorrecta o base dañada.") from exc
    store = key_store if key_store is not None else OSKeyStore()
    identifier = key_id(location)
    previous = store.get(identifier)
    if previous is not None and previous != recovered:
        raise StorageError("Existe otra clave de SO; no sobrescribir silenciosamente.")
    store.put(identifier, recovered)
