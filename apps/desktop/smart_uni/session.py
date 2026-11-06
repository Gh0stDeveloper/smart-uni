"""Estado efímero de sesión de escritorio, separado de la interfaz Tk.

No representa token remoto ni autorización criptográfica del servicio de datos.
La autorización por recurso sigue pendiente para la API futura.
"""

from __future__ import annotations

from collections.abc import Mapping


class SessionState:
    def __init__(self) -> None:
        self._user: dict | None = None

    @property
    def user(self) -> dict | None:
        """Copia de la identidad activa, nunca hash ni contraseña."""
        return dict(self._user) if self._user is not None else None

    def set_user(self, account: Mapping[str, str] | None) -> None:
        if account is None:
            self._user = None
            return
        required = ('name', 'email', 'career')
        if not all(isinstance(account.get(key), str) for key in required):
            raise ValueError('La sesión necesita una identidad de estudiante completa.')
        self._user = {key: account[key] for key in required}

    def logout(self) -> None:
        self._user = None
