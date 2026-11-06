"""API FastAPI de pruebas integradas: identidad OIDC y recursos por propietario.

No se conecta al prototipo Tkinter; no se despliega de forma automática.
Los datos de notes aún NO usan E2EE: solo pruebas sintéticas, no datos reales.
"""
from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from uuid import UUID, uuid4

from fastapi import Depends, FastAPI, Header, HTTPException, Query, Request
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import create_engine, func, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.orm import Session

from .auth import InvalidBearer, OidcVerifier
from .config import Settings
from .models import Identity, Note, RevokedToken


class NoteCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    title: str = Field(min_length=1, max_length=160)
    content: str = Field(default="", max_length=4000)


class NoteUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    title: str = Field(min_length=1, max_length=160)
    content: str = Field(max_length=4000)


class NoteView(BaseModel):
    id: UUID
    title: str
    content: str
    model_config = ConfigDict(from_attributes=True)


class MeView(BaseModel):
    id: UUID
    role: str


def create_app(settings: Settings | None = None, *, verifier: OidcVerifier | None = None, engine=None):
    settings = settings if settings is not None else Settings.from_env()
    engine = engine if engine is not None else create_engine(settings.database_url, pool_pre_ping=True)
    app = FastAPI(
        title="SMART UNI API (prototipo no productivo)",
        version="0.1.0",
        docs_url=None, redoc_url=None, openapi_url=None,
    )
    app.state.engine = engine
    app.state.verifier = verifier if verifier is not None else OidcVerifier(settings)

    def get_session(request: Request):
        with Session(request.app.state.engine) as session:
            yield session

    def authenticated(
        request: Request,
        db: Session = Depends(get_session),
        authorization: str | None = Header(default=None),
    ) -> Identity:
        if not authorization or not authorization.startswith("Bearer ") or authorization.count(" ") != 1:
            raise HTTPException(status_code=401, detail="Bearer OIDC obligatorio", headers={"WWW-Authenticate": "Bearer"})
        raw = authorization[7:]
        try:
            verified = request.app.state.verifier.verify(raw)
        except InvalidBearer:
            raise HTTPException(status_code=401, detail="Credenciales inválidas", headers={"WWW-Authenticate": "Bearer"})
        token_hash = hashlib.sha256(raw.encode("utf-8")).hexdigest()
        if db.get(RevokedToken, token_hash) is not None:
            raise HTTPException(status_code=401, detail="Sesión revocada", headers={"WWW-Authenticate": "Bearer"})
        db.execute(pg_insert(Identity).values(
            id=uuid4(), issuer=verified.issuer, subject=verified.subject, role="student"
        ).on_conflict_do_nothing(constraint="uq_identities_external"))
        db.commit()
        identity = db.scalar(select(Identity).where(
            Identity.issuer == verified.issuer, Identity.subject == verified.subject
        ))
        if identity is None:
            raise HTTPException(status_code=401, detail="Identidad no disponible")
        return identity

    def admin_only(identity: Identity = Depends(authenticated)):
        if identity.role != "admin":
            raise HTTPException(status_code=403, detail="Se necesita autorización administrativa")
        return identity

    @app.get("/healthz")
    def healthz():
        return {"status": "ok", "database": "no comprobada"}

    @app.get("/api/v1/me", response_model=MeView)
    def me(identity: Identity = Depends(authenticated)):
        return MeView(id=identity.id, role=identity.role)

    @app.get("/api/v1/notes", response_model=list[NoteView])
    def list_notes(
        limit: int = Query(default=30, ge=1, le=100),
        offset: int = Query(default=0, ge=0, le=10000),
        identity: Identity = Depends(authenticated),
        db: Session = Depends(get_session),
    ):
        return db.scalars(
            select(Note).where(Note.owner_id == identity.id)
            .order_by(Note.created_at, Note.id)
            .limit(limit).offset(offset)
        ).all()

    @app.post("/api/v1/notes", response_model=NoteView, status_code=201)
    def add_note(
        values: NoteCreate,
        identity: Identity = Depends(authenticated),
        db: Session = Depends(get_session),
    ):
        row = Note(id=uuid4(), owner_id=identity.id, title=values.title, content=values.content)
        db.add(row)
        db.commit()
        db.refresh(row)
        return row

    def owned_note(db: Session, identity: Identity, note_id: UUID):
        note = db.scalar(select(Note).where(Note.id == note_id, Note.owner_id == identity.id))
        if note is None:
            raise HTTPException(status_code=404, detail="Recurso no encontrado")
        return note

    @app.get("/api/v1/notes/{note_id}", response_model=NoteView)
    def get_note(note_id: UUID, identity: Identity = Depends(authenticated), db: Session = Depends(get_session)):
        return owned_note(db, identity, note_id)

    @app.put("/api/v1/notes/{note_id}", response_model=NoteView)
    def update_note(note_id: UUID, values: NoteUpdate, identity: Identity = Depends(authenticated), db: Session = Depends(get_session)):
        note = owned_note(db, identity, note_id)
        note.title, note.content = values.title, values.content
        db.commit()
        db.refresh(note)
        return note

    @app.delete("/api/v1/notes/{note_id}", status_code=204)
    def delete_note(note_id: UUID, identity: Identity = Depends(authenticated), db: Session = Depends(get_session)):
        note = owned_note(db, identity, note_id)
        db.delete(note)
        db.commit()

    @app.get("/api/v1/admin/metrics")
    def metrics(_: Identity = Depends(admin_only), db: Session = Depends(get_session)):
        return {
            "users": db.scalar(select(func.count()).select_from(Identity)),
            "notes": db.scalar(select(func.count()).select_from(Note)),
        }

    @app.post("/api/v1/sessions/revoke", status_code=204)
    def revoke(
        request: Request,
        identity: Identity = Depends(authenticated),
        db: Session = Depends(get_session),
        authorization: str = Header(),
    ):
        raw = authorization[7:]
        verified = request.app.state.verifier.verify(raw)
        token_hash = hashlib.sha256(raw.encode("utf-8")).hexdigest()
        db.execute(pg_insert(RevokedToken).values(
            token_hash=token_hash,
            subject_id=identity.id,
            expires_at=verified.expires_at,
        ).on_conflict_do_nothing())
        db.commit()

    return app


# La app ASGI se crea solo bajo despliegue explícito; nunca se importa desde Tkinter.
app = create_app() if __name__ != "__main__" else None
