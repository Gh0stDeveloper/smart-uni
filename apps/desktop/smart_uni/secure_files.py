"""Materiales cifrados experimentalmente en SQLCipher + motor Rust AEAD.

No genera ninguna copia de plaintext dentro de carpetas de SMART UNI.
La UI aún no permite abrir archivos externos sin crear texto claro temporal;
en modo protegido solo se expone lectura de bytes para un visor futuro.
"""
from __future__ import annotations

import hashlib
import os
import secrets
import tempfile
import uuid
from pathlib import Path

from .core import ValidationError, validate_email
from .offline_queue import OfflineOutbox, make_message
from .secure_crypto import ContentCrypto
from .secure_storage import EncryptedSQLiteRepository, KeyUnavailable, StorageError

MAX_BYTES = 8 * 1024 * 1024
SUFFIXES = {".pdf", ".txt", ".md", ".docx", ".xlsx", ".pptx",
            ".csv", ".png", ".jpg", ".jpeg"}


class SecureMaterialStore:
    """Per-user content key en keyring; DB y archivos ciphertext separados."""

    def __init__(self, repo: EncryptedSQLiteRepository, email: str, *, native=None):
        if not isinstance(repo, EncryptedSQLiteRepository):
            raise StorageError("Se requiere repositorio SQLCipher real.")
        self.repo = repo
        self.email = validate_email(email)
        self.crypto = native if native is not None else ContentCrypto()
        self.folder = repo.path.parent / "encrypted-materials"
        if self.folder.is_symlink():
            raise StorageError("No se admiten directorios enlazados simbólicamente.")
        self._identifier = "content:" + hashlib.sha256(
            (str(repo.path) + "|" + self.email).encode("utf-8")
        ).hexdigest()
        self._keys = repo._keys
        self._key = self._keys.get(self._identifier)
        if self._key is None:
            space = repo.read().get("student_spaces", {}).get(self.email, {})
            if any(item.get("storage") == "suaead1" for item in space.get("materials", [])):
                raise KeyUnavailable(
                    "Falta clave de materiales; importa una recuperación cifrada."
                )
            self._key = secrets.token_bytes(32)
            self._keys.put(self._identifier, self._key)
        if len(self._key) != 32:
            raise KeyUnavailable("La clave de materiales es inválida.")

    @staticmethod
    def _context(email: str, item_id: str) -> bytes:
        owner = hashlib.sha256(email.encode("utf-8")).hexdigest()
        return f"material/{owner}/{item_id}/epoch-1".encode("ascii")

    def _get_item(self, item_id: str) -> dict:
        if not isinstance(item_id, str) or len(item_id) != 32:
            raise StorageError("Identificador de material inválido.")
        space = self.repo.read().get("student_spaces", {}).get(self.email, {})
        for entry in space.get("materials", []):
            if entry.get("id") == item_id and entry.get("storage") == "suaead1":
                return entry
        raise ValidationError("No se encontró un material cifrado de esta cuenta.")

    def _path(self, item_id: str) -> Path:
        if len(item_id) != 32 or any(c not in "0123456789abcdef" for c in item_id):
            raise StorageError("Identificador de material no permitido.")
        return self.folder / (item_id + ".sun1")

    def add(self, subject: str, source: str) -> dict:
        from .student_data import SUBJECTS
        if subject not in SUBJECTS:
            raise ValidationError("Materia desconocida.")
        path = Path(source)
        if path.is_symlink() or not path.is_file():
            raise ValidationError("Selecciona un archivo ordinario válido.")
        if path.suffix.lower() not in SUFFIXES:
            raise ValidationError("Formato no admitido.")
        if path.stat().st_size > MAX_BYTES:
            raise ValidationError("Archivo demasiado grande para la importación protegida.")
        plain = path.read_bytes()
        if len(plain) > MAX_BYTES:
            raise ValidationError("Archivo excede límite seguro.")
        item_id = uuid.uuid4().hex
        context = self._context(self.email, item_id)
        sealed = self.crypto.encrypt(self._key, context, plain)
        if self.folder.is_symlink():
            raise StorageError("El directorio cifrado cambió a enlace simbólico.")
        self.folder.mkdir(mode=0o700, parents=True, exist_ok=True)
        if os.name == "posix":
            os.chmod(self.folder, 0o700)
        dest = self._path(item_id)
        fd, scratch = tempfile.mkstemp(prefix=".encrypted-", suffix=".tmp", dir=self.folder)
        stage = Path(scratch)
        try:
            with os.fdopen(fd, "wb") as output:
                output.write(sealed)
                output.flush()
                os.fsync(output.fileno())
            if dest.exists() or dest.is_symlink():
                raise StorageError("Nombre cifrado ya existente.")
            # Archivo publicado ya cifrado, antes de insertar metadatos.
            os.replace(stage, dest)
            item = {
                "id": item_id, "subject": subject, "title": path.name,
                "file": item_id + ".sun1", "storage": "suaead1",
            }
            msg = make_message("materials.import", self.email, {
                "resource_id": item_id, "subject": subject, "encrypted": True,
            }, entity_id=item_id)

            def change(document):
                if not any(s.get("email") == self.email for s in document["students"]):
                    raise ValidationError("Cuenta no encontrada.")
                space = document.setdefault("student_spaces", {}).setdefault(self.email, {})
                space.setdefault("materials", []).append(item)
                return item

            try:
                saved, result = OfflineOutbox(self.repo).apply(msg, change)
                if not saved:
                    raise StorageError("Operación de material duplicada.")
                return result
            except Exception:
                dest.unlink(missing_ok=True)
                raise
        finally:
            stage.unlink(missing_ok=True)

    def read_bytes(self, item_id: str) -> bytes:
        self._get_item(item_id)
        path = self._path(item_id)
        if path.is_symlink() or not path.is_file() or path.stat().st_size > MAX_BYTES + 300:
            raise StorageError("Archivo cifrado ausente, simbólico o excesivo.")
        return self.crypto.decrypt(self._key, self._context(self.email, item_id), path.read_bytes())

    def delete(self, item_id: str) -> bool:
        self._get_item(item_id)
        path = self._path(item_id)
        msg = make_message("materials.delete", self.email,
            {"resource_id": item_id, "encrypted": True}, entity_id=item_id)

        def remove(document):
            space = document.get("student_spaces", {}).get(self.email, {})
            materials = space.get("materials", [])
            for index, item in enumerate(materials):
                if item.get("id") == item_id and item.get("storage") == "suaead1":
                    del materials[index]
                    return True
            raise StorageError("Archivo ya no existe en el snapshot.")

        saved, changed = OfflineOutbox(self.repo).apply(msg, remove)
        if saved and changed:
            # Un corte tras COMMIT puede dejar un orphan ciphertext, nunca
            # plaintext. Una limpieza de orphans auditada aún está pendiente.
            path.unlink(missing_ok=True)
        return bool(saved and changed)

    def export_recovery(self, phrase: str) -> bytes:
        """Proteger esta copia fuera del equipo; nunca imprimir la frase."""
        return self.crypto.export_recovery(self._key, phrase)

    @classmethod
    def restore_content_key(cls, repo: EncryptedSQLiteRepository, email: str,
                            package: bytes, phrase: str, *, native=None):
        """Restablece la clave perdida; no sobrescribe una clave distinta."""
        clean = validate_email(email)
        cipher = native if native is not None else ContentCrypto()
        key = cipher.restore_recovery(package, phrase)
        identifier = "content:" + hashlib.sha256(
            (str(repo.path) + "|" + clean).encode("utf-8")
        ).hexdigest()
        old = repo._keys.get(identifier)
        if old is not None and old != key:
            raise StorageError("La clave existente difiere de la copia; no sobrescribir.")
        repo._keys.put(identifier, key)
