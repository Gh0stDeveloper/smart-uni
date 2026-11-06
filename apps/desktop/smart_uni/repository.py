"""Puerto de persistencia y adaptador JSON legado (v1), sin cifrado.

Las operaciones mantienen exactamente las semánticas del prototipo. No hay
bloqueo multiproceso, historial ni respaldo automático; etapa 4 cubrirá eso.
"""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from typing import Protocol


class RecordRepository(Protocol):
    """Interfaz usada por servicios; futuras implementaciones requieren pruebas de compatibilidad."""

    path: Path

    def read(self) -> dict: ...

    def write(self, data: dict) -> None: ...


class JsonRepository:
    """Lee y escribe la base JSON local conservando el formato actual."""

    def __init__(self, path: str | Path, initial_data: dict):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if not self.path.exists():
            self.write(initial_data)

    def read(self) -> dict:
        """Cada vez que necesitamos datos, los leemos del archivo JSON."""
        try:
            with self.path.open('r', encoding='utf-8') as fh:
                data = json.load(fh)

            required_fields = ('students', 'courses', 'announcements')
            if not isinstance(data, dict) or not all(
                key in data for key in required_fields
            ):
                raise ValueError('Estructura JSON incompleta')

            return data

        except (OSError, json.JSONDecodeError, ValueError) as exc:
            raise RuntimeError(f'No se pudo leer la base JSON: {exc}') from exc

    def write(self, data: dict) -> None:
        """Guardamos el JSON sin dejar el archivo a medias si algo se interrumpe."""
        # Primero lo escribimos en un archivo temporal y después lo reemplazamos.
        # Esto se conoce como escritura atómica.
        descriptor, temp_name = tempfile.mkstemp(
            prefix='.smartuni-',
            suffix='.json',
            dir=self.path.parent,
        )

        try:
            with os.fdopen(descriptor, 'w', encoding='utf-8') as fh:
                json.dump(data, fh, ensure_ascii=False, indent=2)
                fh.write('\n')
                fh.flush()
                os.fsync(fh.fileno())

            os.replace(temp_name, self.path)

        finally:
            if os.path.exists(temp_name):
                os.unlink(temp_name)

