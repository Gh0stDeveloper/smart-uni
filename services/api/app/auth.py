"""Validación de JWT RS256 OIDC con issuer/aud y JWKS estático del entorno.

No confía en role/email/actor_ref del JWT para autorización; el rol se lee de
PostgreSQL. No soporta tokens opacos; exigir access tokens JWT del proveedor.
"""
from dataclasses import dataclass
from datetime import datetime, timezone

import jwt
from jwt import PyJWKClient

from .config import Settings


@dataclass(frozen=True)
class VerifiedIdentity:
    issuer: str
    subject: str
    expires_at: datetime


class OidcVerifier:
    def __init__(self, settings: Settings, *, key_client=None):
        self.settings = settings
        self.key_client = key_client if key_client is not None else PyJWKClient(
            settings.oidc_jwks_url, cache_jwk_set=True, lifespan=300, timeout=5
        )

    def verify(self, token: str) -> VerifiedIdentity:
        try:
            if not token or len(token) > 16384:
                raise ValueError("Bearer vacío o excesivo")
            # NO confiar en jku/x5u/JWKS indicados en cabeceras de tokens.
            signing_key = self.key_client.get_signing_key_from_jwt(token)
            payload = jwt.decode(
                token,
                signing_key.key,
                algorithms=["RS256"],
                audience=self.settings.oidc_audience,
                issuer=self.settings.oidc_issuer,
                options={"require": ["iss", "sub", "aud", "exp", "iat"]},
                leeway=30,
            )
            sub = payload["sub"]
            if not isinstance(sub, str) or not 1 <= len(sub) <= 255:
                raise ValueError("sub no válido")
            if not isinstance(payload["exp"], (int, float)):
                raise ValueError("exp no válido")
            return VerifiedIdentity(
                issuer=self.settings.oidc_issuer,
                subject=sub,
                expires_at=datetime.fromtimestamp(payload["exp"], tz=timezone.utc),
            )
        except Exception as exc:
            # No devolver detalles de JWT ni endpoints en HTTP.
            raise InvalidBearer("Token OIDC inválido") from exc


class InvalidBearer(ValueError):
    pass
