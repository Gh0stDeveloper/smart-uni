"""Integración con PostgreSQL real y JWT RS256 firmados (sin IdP remoto).

Las identidades, firmas y contenidos son exclusivamente sintéticos.
"""
import os
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from uuid import UUID

import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import rsa
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select, text
from sqlalchemy.orm import Session

from services.api.app.auth import OidcVerifier
from services.api.app.config import Settings
from services.api.app.main import create_app
from services.api.app.models import Identity

ISSUER = "https://issuer.smartuni.invalid/realms/test"
AUDIENCE = "smartuni-api"
PRIVATE = rsa.generate_private_key(public_exponent=65537, key_size=2048)


class FixtureJWKS:
    def get_signing_key_from_jwt(self, token):
        header = jwt.get_unverified_header(token)
        if header.get("kid") != "fixture1":
            raise ValueError("kid desconocido")
        return SimpleNamespace(key=PRIVATE.public_key())


def make_token(sub="alumno-A", *, role="student", issuer=ISSUER, audience=AUDIENCE,
               seconds=3600, secret_key=None):
    now = datetime.now(timezone.utc)
    payload = {
        "iss": issuer, "sub": sub, "aud": audience,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(seconds=seconds)).timestamp()),
        "role": role,  # Este campo es NO confiable.
    }
    if secret_key is not None:
        return jwt.encode(payload, secret_key, algorithm="HS256", headers={"kid": "fixture1"})
    return jwt.encode(payload, PRIVATE, algorithm="RS256", headers={"kid": "fixture1"})


@pytest.fixture
def setup():
    dburl = os.environ["DATABASE_URL"]
    settings = Settings(dburl, ISSUER, AUDIENCE, ISSUER + "/certs")
    engine = create_engine(dburl)
    with engine.begin() as db:
        db.execute(text("TRUNCATE TABLE revoked_tokens, notes, identities RESTART IDENTITY CASCADE"))
    verifier = OidcVerifier(settings, key_client=FixtureJWKS())
    app = create_app(settings, verifier=verifier, engine=engine)
    with TestClient(app) as client:
        yield client, engine
    engine.dispose()


def headers(token):
    return {"Authorization": "Bearer " + token}


def test_liveness_and_no_anonymous_access(setup):
    client, _ = setup
    assert client.get("/healthz").status_code == 200
    assert client.get("/api/v1/me").status_code == 401
    assert client.post("/api/v1/notes", json={"title": "a"}).status_code == 401
    assert client.get("/api/v1/notes", headers={"X-Actor-Ref": "admin@uni.edu"}).status_code == 401


@pytest.mark.parametrize("token", [
    make_token(issuer="https://evil.invalid"),
    make_token(audience="wrong-api"),
    make_token(seconds=-3600),
    make_token(secret_key="fake-signing-key"),
])
def test_invalid_signature_issuer_audience_expiration_fail_closed(setup, token):
    client, _ = setup
    assert client.get("/api/v1/me", headers=headers(token)).status_code == 401


def test_owner_isolation_and_not_using_client_actor(setup):
    client, _ = setup
    token_a, token_b = make_token("student-a"), make_token("student-b")
    created = client.post("/api/v1/notes", headers=headers(token_a),
                          json={"title": "Sintético privado A", "content": "Solo A"})
    assert created.status_code == 201, created.text
    item = created.json()
    assert client.get("/api/v1/notes", headers=headers(token_b)).json() == []
    for method, body in [("get", None), ("put", {"title": "Robo", "content": "no"}), ("delete", None)]:
        resp = getattr(client, method)(
            "/api/v1/notes/" + item["id"], headers={**headers(token_b), "X-Actor-Ref": "student-a"},
            **({"json": body} if body is not None else {}),
        )
        assert resp.status_code == 404
    own = client.get("/api/v1/notes/" + item["id"], headers=headers(token_a))
    assert own.status_code == 200 and own.json()["content"] == "Solo A"
    changed = client.put("/api/v1/notes/" + item["id"], headers=headers(token_a),
                         json={"title": "Actualizado", "content": "Nuevo"})
    assert changed.status_code == 200
    assert client.delete("/api/v1/notes/" + item["id"], headers=headers(token_a)).status_code == 204
    assert client.get("/api/v1/notes", headers=headers(token_a)).json() == []


def test_role_is_only_database_assigned(setup):
    client, engine = setup
    token = make_token("student-c", role="admin")
    assert client.get("/api/v1/me", headers=headers(token)).json()["role"] == "student"
    assert client.get("/api/v1/admin/metrics", headers=headers(token)).status_code == 403
    with Session(engine) as session:
        account = session.scalar(select(Identity).where(Identity.subject == "student-c"))
        assert account is not None
        account.role = "admin"  # Cambio de operador DB, NO de JWT.
        session.commit()
    metrics = client.get("/api/v1/admin/metrics", headers=headers(token))
    assert metrics.status_code == 200
    assert metrics.json()["users"] >= 1


def test_sql_injection_treated_as_data(setup):
    client, engine = setup
    token = make_token("student-injection' OR 1=1 --")
    payload = "test' OR 1=1 --"
    response = client.post("/api/v1/notes", headers=headers(token),
                           json={"title": payload, "content": "solo texto sintético"})
    assert response.status_code == 201
    assert client.get("/api/v1/notes", headers=headers(token)).json()[0]["title"] == payload
    other = make_token("other")
    assert client.get("/api/v1/notes", headers=headers(other)).json() == []


def test_revocation_is_immediate_only_for_this_service(setup):
    client, _ = setup
    token = make_token("student-revocation")
    assert client.get("/api/v1/me", headers=headers(token)).status_code == 200
    assert client.post("/api/v1/sessions/revoke", headers=headers(token)).status_code == 204
    assert client.get("/api/v1/me", headers=headers(token)).status_code == 401


def test_request_validation_and_foreign_resource_404(setup):
    client, _ = setup
    tok = make_token("synthetic-user")
    assert client.post("/api/v1/notes", headers=headers(tok),
                       json={"title": "", "content": ""}).status_code == 422
    assert client.post("/api/v1/notes", headers=headers(tok),
                       json={"title": "valid", "owner_id": "forged"}).status_code == 422
    assert client.get("/api/v1/notes/00000000-0000-0000-0000-000000000001",
                      headers=headers(tok)).status_code == 404


def test_configuration_rejects_untrusted_protocol_and_db():
    with pytest.raises(ValueError):
        Settings("sqlite:///local.db", ISSUER, AUDIENCE, ISSUER + "/certs")
    with pytest.raises(ValueError):
        Settings("postgresql+psycopg://x/y", "http://issuer.invalid", AUDIENCE, ISSUER + "/certs")
