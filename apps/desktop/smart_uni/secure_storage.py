"""SQLCipher opt-in: no se permite degradación a sqlite3 sin cifrado.

La base SQLite se cifra; la app Tkinter existente sigue por defecto en JSON.
La clave de 32 bytes se custodia en un almacén autorizado del SO, o en el
almacén de pruebas inyectado expresamente. No implementa E2EE ni cifrado de materiales.
"""
from __future__ import annotations

import hashlib
import json
import os
import secrets
from contextlib import closing
from pathlib import Path
from typing import Protocol


class StorageError(RuntimeError):
    """Fallo de almacenamiento seguro sin degradación silenciosa."""


class KeyUnavailable(StorageError):
    """No está disponible o se perdió la clave del almacén seguro."""


class KeyStore(Protocol):
    def get(self, identifier: str) -> bytes | None: ...
    def put(self, identifier: str, key: bytes) -> None: ...


class OSKeyStore:
    """Solo backends reconocidos de almacén de credenciales del sistema."""
    _SAFE = (
        "keyring.backends.Windows",
        "keyring.backends.SecretService",
        "keyring.backends.kwallet",
        "keyring.backends.macOS",
    )

    @staticmethod
    def _service():
        try:
            import keyring
        except ImportError as exc:
            raise KeyUnavailable("Instala keyring y configura el almacén seguro del SO.") from exc
        backend = keyring.get_keyring()
        if not backend.__class__.__module__.startswith(OSKeyStore._SAFE):
            raise KeyUnavailable("Backend de keyring no seguro o sin sesión de escritorio.")
        return keyring

    def get(self, identifier: str) -> bytes | None:
        try:
            encoded = self._service().get_password("smart-uni-2.0", identifier)
            if encoded is None:
                return None
            key = bytes.fromhex(encoded)
            if len(key) != 32:
                raise KeyUnavailable("Clave recuperada inválida.")
            return key
        except KeyUnavailable:
            raise
        except Exception as exc:
            raise KeyUnavailable("No se pudo leer la clave del SO.") from exc

    def put(self, identifier: str, key: bytes) -> None:
        if len(key) != 32:
            raise KeyUnavailable("La clave SQLCipher debe medir 32 bytes.")
        try:
            self._service().set_password("smart-uni-2.0", identifier, key.hex())
        except KeyUnavailable:
            raise
        except Exception as exc:
            raise KeyUnavailable("No se pudo guardar la clave en el SO.") from exc


def key_id(path: Path) -> str:
    return "database:" + hashlib.sha256(os.fsencode(str(path.resolve()))).hexdigest()


def cipher_driver():
    try:
        from sqlcipher3 import dbapi2 as sqlcipher
        return sqlcipher
    except ImportError as exc:
        raise StorageError("Instala requirements-secure.txt; sqlite3 no es sustituto.") from exc


def validate_snapshot(data: dict) -> None:
    if not isinstance(data, dict) or type(data.get("version")) is not int or data["version"] != 1:
        raise StorageError("Solo se admite el formato JSON v1.")
    for field in ("students", "courses", "announcements"):
        if not isinstance(data.get(field), list):
            raise StorageError("Falta una lista obligatoria del JSON: " + field)
    if "student_spaces" in data and not isinstance(data["student_spaces"], dict):
        raise StorageError("student_spaces inválido.")
    try:
        encoded = json.dumps(data, ensure_ascii=False, allow_nan=False)
    except (TypeError, ValueError) as exc:
        raise StorageError("Contenido JSON inválido.") from exc
    if len(encoded.encode("utf-8")) > 20 * 1024 * 1024:
        raise StorageError("Snapshot supera 20 MiB.")


class EncryptedSQLiteRepository:
    """Puerto read/write compatible; snapshot + outbox usan transacciones.

    Modo DELETE evita respaldos incompletos por WAL; no elimina el JSON legado.
    """
    def __init__(self, path, initial_data, *, key_store: KeyStore | None = None, identity_path=None):
        raw_path = Path(path).expanduser()
        if raw_path.is_symlink():
            raise StorageError("No se admiten bases enlazadas simbólicamente.")
        self.path = raw_path.resolve()
        validate_snapshot(initial_data)
        self.path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
        self._driver = cipher_driver()
        self._keys = key_store if key_store is not None else OSKeyStore()
        self._identity = key_id(Path(identity_path) if identity_path else self.path)
        exists = self.path.exists()
        self._key = self._keys.get(self._identity)
        if self._key is None:
            if exists:
                raise KeyUnavailable("Base existente sin clave; prohibido generar otra.")
            self._key = secrets.token_bytes(32)
            self._keys.put(self._identity, self._key)
        if len(self._key) != 32:
            raise KeyUnavailable("Clave de longitud inválida.")
        with closing(self._connection()) as con:
            self._schema(con, initial_data)
        if os.name == "posix":
            os.chmod(self.path, 0o600)

    def _connection(self):
        con = self._driver.connect(str(self.path), isolation_level=None, timeout=15)
        try:
            # Solo interpolamos hex de clave validada, nunca entrada de usuario.
            con.execute("PRAGMA key = \"x'" + self._key.hex() + "'\"")
            row = con.execute("PRAGMA cipher_version").fetchone()
            if not row or not row[0]:
                raise StorageError("El módulo cargado no proporciona SQLCipher.")
            con.execute("SELECT count(*) FROM sqlite_master").fetchone()
            con.execute("PRAGMA foreign_keys=ON")
            con.execute("PRAGMA journal_mode=DELETE")
            con.execute("PRAGMA synchronous=FULL")
            con.execute("PRAGMA secure_delete=ON")
            con.execute("PRAGMA temp_store=MEMORY")
            return con
        except Exception as exc:
            con.close()
            raise StorageError("No se pudo verificar SQLCipher: clave o base inválida.") from exc

    @staticmethod
    def _schema(con, initial):
        con.execute("BEGIN IMMEDIATE")
        try:
            con.execute("CREATE TABLE IF NOT EXISTS snapshot (id INTEGER PRIMARY KEY CHECK(id=1), document TEXT NOT NULL)")
            con.execute(
                "CREATE TABLE IF NOT EXISTS outbox ("
                "seq INTEGER PRIMARY KEY AUTOINCREMENT,"
                "operation_id TEXT NOT NULL UNIQUE,"
                "operation_type TEXT NOT NULL,"
                "message TEXT NOT NULL,"
                "state TEXT NOT NULL DEFAULT 'pending' CHECK(state IN ('pending','error')),"
                "attempts INTEGER NOT NULL DEFAULT 0)"
            )
            con.execute("CREATE TABLE IF NOT EXISTS metadata (key TEXT PRIMARY KEY, value TEXT NOT NULL)")
            con.execute("INSERT OR IGNORE INTO snapshot (id,document) VALUES (1,?)",
                        (json.dumps(initial, ensure_ascii=False, allow_nan=False),))
            con.execute("PRAGMA user_version=1")
            con.execute("COMMIT")
        except Exception:
            con.execute("ROLLBACK")
            raise

    def read(self) -> dict:
        with closing(self._connection()) as con:
            row = con.execute("SELECT document FROM snapshot WHERE id=1").fetchone()
            if row is None:
                raise StorageError("No existe el snapshot.")
            value = json.loads(row[0])
            validate_snapshot(value)
            return value

    def write(self, data: dict) -> None:
        """Compatibilidad: no crea evento sincronizable ni presume ACK remoto."""
        validate_snapshot(data)
        with closing(self._connection()) as con:
            con.execute("BEGIN IMMEDIATE")
            try:
                con.execute("UPDATE snapshot SET document=? WHERE id=1",
                            (json.dumps(data, ensure_ascii=False, allow_nan=False),))
                con.execute("COMMIT")
            except Exception:
                con.execute("ROLLBACK")
                raise

    def integrity_check(self):
        with closing(self._connection()) as con:
            row = con.execute("PRAGMA integrity_check").fetchone()
            if not row or row[0] != "ok":
                raise StorageError("PRAGMA integrity_check no pasó.")
