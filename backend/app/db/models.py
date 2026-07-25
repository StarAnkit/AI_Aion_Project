import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.domain.rights import CC0_LICENSE_URI


class SourceProvider(Base):
    __tablename__ = "source_provider"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    code: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    base_url: Mapped[str] = mapped_column(Text, nullable=False)
    rights_policy_version: Mapped[str] = mapped_column(String(64), nullable=False)
    is_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    source_records: Mapped[list["SourceRecord"]] = relationship(back_populates="provider")


class SourceRecord(Base):
    __tablename__ = "source_record"
    __table_args__ = (
        UniqueConstraint("provider_id", "external_id", name="uq_source_record_provider_external"),
        CheckConstraint(
            "payload_sha256 ~ '^[0-9a-f]{64}$'", name="ck_source_record_payload_sha256"
        ),
        Index("ix_source_record_provider_id", "provider_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    provider_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("source_provider.id", ondelete="RESTRICT"), nullable=False
    )
    external_id: Mapped[str] = mapped_column(String(255), nullable=False)
    source_url: Mapped[str] = mapped_column(Text, nullable=False)
    raw_facts: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    payload_sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    upstream_updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    ingested_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    provider: Mapped[SourceProvider] = relationship(back_populates="source_records")
    artwork: Mapped["Artwork | None"] = relationship(back_populates="source_record")
    rights_evidence: Mapped[list["RightsEvidence"]] = relationship(back_populates="source_record")


class Artwork(Base):
    __tablename__ = "artwork"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    source_record_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("source_record.id", ondelete="RESTRICT"),
        nullable=False,
        unique=True,
    )
    title: Mapped[str] = mapped_column(Text, nullable=False)
    creator_display: Mapped[str | None] = mapped_column(Text)
    date_text: Mapped[str | None] = mapped_column(Text)
    medium: Mapped[str | None] = mapped_column(Text)
    culture: Mapped[str | None] = mapped_column(Text)
    department: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    source_record: Mapped[SourceRecord] = relationship(back_populates="artwork")
    media_assets: Mapped[list["MediaAsset"]] = relationship(back_populates="artwork")


class MediaAsset(Base):
    __tablename__ = "media_asset"
    __table_args__ = (
        UniqueConstraint("artwork_id", "source_url", name="uq_media_asset_artwork_source_url"),
        CheckConstraint("width IS NULL OR width > 0", name="ck_media_asset_width_positive"),
        CheckConstraint("height IS NULL OR height > 0", name="ck_media_asset_height_positive"),
        CheckConstraint(
            "publication_state IN ('hidden', 'published', 'revoked')",
            name="ck_media_asset_publication_state",
        ),
        CheckConstraint(
            "rights_status IN ('pending', 'approved', 'rejected', 'conflicting')",
            name="ck_media_asset_rights_status",
        ),
        CheckConstraint(
            "publication_state <> 'published' OR "
            f"(rights_status = 'approved' AND license_uri = '{CC0_LICENSE_URI}')",
            name="ck_media_asset_published_requires_cc0",
        ),
        Index("ix_media_asset_publication_state", "publication_state"),
        Index("ix_media_asset_artwork_id", "artwork_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    artwork_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("artwork.id", ondelete="CASCADE"), nullable=False
    )
    source_url: Mapped[str] = mapped_column(Text, nullable=False)
    media_type: Mapped[str] = mapped_column(String(32), nullable=False, default="image")
    mime_type: Mapped[str | None] = mapped_column(String(100))
    width: Mapped[int | None] = mapped_column(Integer)
    height: Mapped[int | None] = mapped_column(Integer)
    rights_status: Mapped[str] = mapped_column(String(32), nullable=False, default="pending")
    license_uri: Mapped[str | None] = mapped_column(Text)
    publication_state: Mapped[str] = mapped_column(String(32), nullable=False, default="hidden")
    rights_checked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    artwork: Mapped[Artwork] = relationship(back_populates="media_assets")
    rights_evidence: Mapped[list["RightsEvidence"]] = relationship(back_populates="media_asset")


class RightsEvidence(Base):
    __tablename__ = "rights_evidence"
    __table_args__ = (
        CheckConstraint(
            "(source_record_id IS NOT NULL)::integer + (media_asset_id IS NOT NULL)::integer = 1",
            name="ck_rights_evidence_one_subject",
        ),
        Index("ix_rights_evidence_source_record_id", "source_record_id"),
        Index("ix_rights_evidence_media_asset_id", "media_asset_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    source_record_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("source_record.id", ondelete="CASCADE")
    )
    media_asset_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("media_asset.id", ondelete="CASCADE")
    )
    asserted_status: Mapped[str] = mapped_column(String(64), nullable=False)
    license_uri: Mapped[str | None] = mapped_column(Text)
    evidence_field: Mapped[str] = mapped_column(String(255), nullable=False)
    evidence_value: Mapped[str | None] = mapped_column(Text)
    evidence_url: Mapped[str] = mapped_column(Text, nullable=False)
    policy_version: Mapped[str] = mapped_column(String(64), nullable=False)
    is_conflicting: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    observed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    source_record: Mapped[SourceRecord | None] = relationship(back_populates="rights_evidence")
    media_asset: Mapped[MediaAsset | None] = relationship(back_populates="rights_evidence")
