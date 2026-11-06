"""Configuración obligatoria del backend. No permite DB SQLite ni OIDC HTTP."""
from dataclasses import dataclass
import os
from urllib.parse import urlsplit
from sqlalchemy.engine.url import make_url


@dataclass(frozen=True)
class Settings:
    database_url: str
    oidc_issuer: str
    oidc_audience: str
    oidc_jwks_url: str
    allow_legacy_plaintext_notes: bool = False

    def __post_init__(self):
        if not self.database_url.startswith("postgresql+psycopg://"):
            raise ValueError("DATABASE_URL requiere PostgreSQL + psycopg, sin SQLite fallback")
        if not self.oidc_audience or len(self.oidc_audience) > 200:
            raise ValueError("OIDC_AUDIENCE obligatorio")
        for name, url in (("OIDC_ISSUER", self.oidc_issuer), ("OIDC_JWKS_URL", self.oidc_jwks_url)):
            parsed = urlsplit(url)
            if parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password or parsed.fragment:
                raise ValueError(name + " debe ser URL HTTPS confiable y sin credenciales")
        if "?" in self.oidc_issuer or "#" in self.oidc_issuer:
            raise ValueError("OIDC_ISSUER no admite parámetros")
        # El CRUD v1 en claro solo puede habilitarse en laboratorio aislado.
        # No basta con una variable de entorno accidental en producción.
        if self.allow_legacy_plaintext_notes:
            issuer_host = urlsplit(self.oidc_issuer).hostname or ""
            db_host = make_url(self.database_url).host
            if not issuer_host.endswith(".invalid") or db_host not in ("localhost", "127.0.0.1", "::1"):
                raise ValueError("Notas demo plaintext solo con IdP sintético y PostgreSQL local")


    @classmethod
    def from_env(cls):
        return cls(
            database_url=os.environ["DATABASE_URL"],
            oidc_issuer=os.environ["OIDC_ISSUER"].rstrip("/"),
            oidc_audience=os.environ["OIDC_AUDIENCE"],
            oidc_jwks_url=os.environ["OIDC_JWKS_URL"],
            allow_legacy_plaintext_notes=os.environ.get("SMARTUNI_DEMO_PLAINTEXT_NOTES") == "1",
        )
