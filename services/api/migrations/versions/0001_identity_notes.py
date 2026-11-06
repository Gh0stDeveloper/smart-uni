"""Esquema de identidad OIDC, notas y revocación de sesiones.

Revision ID: 0001_identity_notes
Revises:
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0001_identity_notes"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "identities",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("issuer", sa.String(512), nullable=False),
        sa.Column("subject", sa.String(255), nullable=False),
        sa.Column("role", sa.String(16), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("role IN ('student','admin')", name="ck_identity_role"),
        sa.UniqueConstraint("issuer", "subject", name="uq_identities_external"),
    )
    op.create_table(
        "notes",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("owner_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("identities.id", ondelete="CASCADE"), nullable=False),
        sa.Column("title", sa.String(160), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_notes_owner_created", "notes", ["owner_id", "created_at"])
    op.create_table(
        "revoked_tokens",
        sa.Column("token_hash", sa.String(64), primary_key=True),
        sa.Column("subject_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("identities.id", ondelete="CASCADE"), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_revoked_token_expiry", "revoked_tokens", ["expires_at"])


def downgrade():
    op.drop_index("ix_revoked_token_expiry", table_name="revoked_tokens")
    op.drop_table("revoked_tokens")
    op.drop_index("ix_notes_owner_created", table_name="notes")
    op.drop_table("notes")
    op.drop_table("identities")
