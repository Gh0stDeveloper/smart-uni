"""Encrypted synchronization log, immutable revisions, durable conflicts and resumable blobs.

Revision ID: 0002_sync
Revises: 0001_identity_notes
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0002_sync"
down_revision = "0001_identity_notes"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "sync_owner_state",
        sa.Column("owner_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("identities.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("cursor", sa.BigInteger(), nullable=False),
    )
    op.create_table(
        "sync_resources",
        sa.Column("owner_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("identities.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("resource_id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("revision", sa.BigInteger(), nullable=False),
        sa.Column("deleted", sa.Boolean(), nullable=False),
        sa.CheckConstraint("revision > 0", name="ck_sync_resource_revision"),
    )
    op.create_table(
        "sync_versions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("owner_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("identities.id", ondelete="CASCADE"), nullable=False),
        sa.Column("resource_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("operation_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("request_hash", sa.String(64), nullable=False),
        sa.Column("cursor", sa.BigInteger(), nullable=False),
        sa.Column("revision", sa.BigInteger(), nullable=False),
        sa.Column("epoch", sa.BigInteger(), nullable=False),
        sa.Column("deleted", sa.Boolean(), nullable=False),
        sa.Column("ciphertext", sa.LargeBinary(), nullable=True),
        sa.Column("blob_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("owner_id", "cursor", name="uq_sync_version_owner_cursor"),
        sa.UniqueConstraint("owner_id", "operation_id", name="uq_sync_version_owner_operation"),
        sa.CheckConstraint("revision > 0", name="ck_sync_version_revision"),
    )
    op.create_index("ix_sync_versions_pull", "sync_versions", ["owner_id", "cursor"])
    op.create_table(
        "sync_conflicts",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("owner_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("identities.id", ondelete="CASCADE"), nullable=False),
        sa.Column("resource_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("operation_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("request_hash", sa.String(64), nullable=False),
        sa.Column("base_revision", sa.BigInteger(), nullable=False),
        sa.Column("server_revision", sa.BigInteger(), nullable=False),
        sa.Column("epoch", sa.BigInteger(), nullable=False),
        sa.Column("deleted", sa.Boolean(), nullable=False),
        sa.Column("ciphertext", sa.LargeBinary(), nullable=True),
        sa.Column("resolved", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("owner_id", "operation_id", name="uq_sync_conflict_owner_operation"),
    )
    op.create_index("ix_sync_conflicts_owner", "sync_conflicts", ["owner_id", "resolved"])
    op.create_table(
        "sync_blobs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("owner_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("identities.id", ondelete="CASCADE"), nullable=False),
        sa.Column("resource_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("epoch", sa.BigInteger(), nullable=False),
        sa.Column("total_size", sa.Integer(), nullable=False),
        sa.Column("sha256", sa.String(64), nullable=False),
        sa.Column("complete", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("total_size > 0 AND total_size <= 8389000", name="ck_sync_blob_size"),
    )
    op.create_table(
        "sync_blob_parts",
        sa.Column("blob_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("sync_blobs.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("part_index", sa.Integer(), primary_key=True),
        sa.Column("sha256", sa.String(64), nullable=False),
        sa.Column("data", sa.LargeBinary(), nullable=False),
        sa.CheckConstraint("part_index >= 0", name="ck_sync_part_index"),
    )


def downgrade():
    op.drop_table("sync_blob_parts")
    op.drop_table("sync_blobs")
    op.drop_index("ix_sync_conflicts_owner", table_name="sync_conflicts")
    op.drop_table("sync_conflicts")
    op.drop_index("ix_sync_versions_pull", table_name="sync_versions")
    op.drop_table("sync_versions")
    op.drop_table("sync_resources")
    op.drop_table("sync_owner_state")
