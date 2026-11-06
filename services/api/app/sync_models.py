"""Versioned ciphertext-only synchronization. Never persist plaintext or keys."""
from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import (
    BigInteger, Boolean, CheckConstraint, DateTime, ForeignKey, ForeignKeyConstraint,
    Index, Integer, LargeBinary, String, UniqueConstraint, func,
)
from sqlalchemy.dialects.postgresql import UUID as PgUUID
from sqlalchemy.orm import Mapped, mapped_column

from .models import Base


class SyncOwnerState(Base):
    __tablename__ = "sync_owner_state"

    owner_id: Mapped[UUID] = mapped_column(
        PgUUID(as_uuid=True), ForeignKey("identities.id", ondelete="CASCADE"), primary_key=True
    )
    cursor: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0)


class SyncResource(Base):
    __tablename__ = "sync_resources"
    __table_args__ = (
        CheckConstraint("revision > 0", name="ck_sync_resource_revision"),
    )
    owner_id: Mapped[UUID] = mapped_column(
        PgUUID(as_uuid=True), ForeignKey("identities.id", ondelete="CASCADE"), primary_key=True
    )
    resource_id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), primary_key=True)
    revision: Mapped[int] = mapped_column(BigInteger, nullable=False)
    deleted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)


class SyncVersion(Base):
    __tablename__ = "sync_versions"
    __table_args__ = (
        UniqueConstraint("owner_id", "cursor", name="uq_sync_version_owner_cursor"),
        UniqueConstraint("owner_id", "operation_id", name="uq_sync_version_owner_operation"),
        Index("ix_sync_versions_pull", "owner_id", "cursor"),
        CheckConstraint("revision > 0", name="ck_sync_version_revision"),
    )
    id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), primary_key=True, default=uuid4)
    owner_id: Mapped[UUID] = mapped_column(
        PgUUID(as_uuid=True), ForeignKey("identities.id", ondelete="CASCADE"), nullable=False
    )
    resource_id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), nullable=False)
    operation_id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), nullable=False)
    request_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    cursor: Mapped[int] = mapped_column(BigInteger, nullable=False)
    revision: Mapped[int] = mapped_column(BigInteger, nullable=False)
    epoch: Mapped[int] = mapped_column(BigInteger, nullable=False)
    deleted: Mapped[bool] = mapped_column(Boolean, nullable=False)
    ciphertext: Mapped[bytes | None] = mapped_column(LargeBinary, nullable=True)
    blob_id: Mapped[UUID | None] = mapped_column(PgUUID(as_uuid=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class SyncConflict(Base):
    __tablename__ = "sync_conflicts"
    __table_args__ = (
        UniqueConstraint("owner_id", "operation_id", name="uq_sync_conflict_owner_operation"),
        Index("ix_sync_conflicts_owner", "owner_id", "resolved"),
    )
    id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), primary_key=True, default=uuid4)
    owner_id: Mapped[UUID] = mapped_column(
        PgUUID(as_uuid=True), ForeignKey("identities.id", ondelete="CASCADE"), nullable=False
    )
    resource_id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), nullable=False)
    operation_id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), nullable=False)
    request_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    base_revision: Mapped[int] = mapped_column(BigInteger, nullable=False)
    server_revision: Mapped[int] = mapped_column(BigInteger, nullable=False)
    epoch: Mapped[int] = mapped_column(BigInteger, nullable=False)
    deleted: Mapped[bool] = mapped_column(Boolean, nullable=False)
    ciphertext: Mapped[bytes | None] = mapped_column(LargeBinary, nullable=True)
    resolved: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class SyncBlob(Base):
    __tablename__ = "sync_blobs"
    __table_args__ = (
        CheckConstraint("total_size > 0 AND total_size <= 8389000", name="ck_sync_blob_size"),
    )
    id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), primary_key=True)
    owner_id: Mapped[UUID] = mapped_column(
        PgUUID(as_uuid=True), ForeignKey("identities.id", ondelete="CASCADE"), nullable=False
    )
    resource_id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), nullable=False)
    epoch: Mapped[int] = mapped_column(BigInteger, nullable=False)
    base_revision: Mapped[int] = mapped_column(BigInteger, nullable=False)
    total_size: Mapped[int] = mapped_column(Integer, nullable=False)
    sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    complete: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class SyncBlobPart(Base):
    __tablename__ = "sync_blob_parts"
    __table_args__ = (
        ForeignKeyConstraint(["blob_id"], ["sync_blobs.id"], ondelete="CASCADE"),
        CheckConstraint("part_index >= 0", name="ck_sync_part_index"),
    )
    blob_id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), primary_key=True)
    part_index: Mapped[int] = mapped_column(Integer, primary_key=True)
    sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    data: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)
