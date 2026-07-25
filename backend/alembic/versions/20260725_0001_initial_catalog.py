"""Create provider-neutral rights-safe catalog tables.

Revision ID: 20260725_0001
Revises: None
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "20260725_0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None
CC0_LICENSE_URI = "https://creativecommons.org/publicdomain/zero/1.0/"


def upgrade() -> None:
    op.create_table(
        "source_provider",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("code", sa.String(64), nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("base_url", sa.Text(), nullable=False),
        sa.Column("rights_policy_version", sa.String(64), nullable=False),
        sa.Column("is_enabled", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.UniqueConstraint("code", name="uq_source_provider_code"),
    )
    op.create_table(
        "source_record",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("provider_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("external_id", sa.String(255), nullable=False),
        sa.Column("source_url", sa.Text(), nullable=False),
        sa.Column("raw_facts", postgresql.JSONB(), nullable=False),
        sa.Column("payload_sha256", sa.String(64), nullable=False),
        sa.Column("upstream_updated_at", sa.DateTime(timezone=True)),
        sa.Column(
            "ingested_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.CheckConstraint(
            "payload_sha256 ~ '^[0-9a-f]{64}$'", name="ck_source_record_payload_sha256"
        ),
        sa.ForeignKeyConstraint(["provider_id"], ["source_provider.id"], ondelete="RESTRICT"),
        sa.UniqueConstraint(
            "provider_id", "external_id", name="uq_source_record_provider_external"
        ),
    )
    op.create_index("ix_source_record_provider_id", "source_record", ["provider_id"])
    op.create_table(
        "artwork",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("source_record_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("creator_display", sa.Text()),
        sa.Column("date_text", sa.Text()),
        sa.Column("medium", sa.Text()),
        sa.Column("culture", sa.Text()),
        sa.Column("department", sa.Text()),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.ForeignKeyConstraint(["source_record_id"], ["source_record.id"], ondelete="RESTRICT"),
        sa.UniqueConstraint("source_record_id", name="uq_artwork_source_record_id"),
    )
    op.create_table(
        "media_asset",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("artwork_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("source_url", sa.Text(), nullable=False),
        sa.Column("media_type", sa.String(32), nullable=False, server_default="image"),
        sa.Column("mime_type", sa.String(100)),
        sa.Column("width", sa.Integer()),
        sa.Column("height", sa.Integer()),
        sa.Column("rights_status", sa.String(32), nullable=False, server_default="pending"),
        sa.Column("license_uri", sa.Text()),
        sa.Column("publication_state", sa.String(32), nullable=False, server_default="hidden"),
        sa.Column("rights_checked_at", sa.DateTime(timezone=True)),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.CheckConstraint("width IS NULL OR width > 0", name="ck_media_asset_width_positive"),
        sa.CheckConstraint("height IS NULL OR height > 0", name="ck_media_asset_height_positive"),
        sa.CheckConstraint(
            "publication_state IN ('hidden', 'published', 'revoked')",
            name="ck_media_asset_publication_state",
        ),
        sa.CheckConstraint(
            "rights_status IN ('pending', 'approved', 'rejected', 'conflicting')",
            name="ck_media_asset_rights_status",
        ),
        sa.CheckConstraint(
            "publication_state <> 'published' OR "
            f"(rights_status = 'approved' AND license_uri = '{CC0_LICENSE_URI}')",
            name="ck_media_asset_published_requires_cc0",
        ),
        sa.ForeignKeyConstraint(["artwork_id"], ["artwork.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("artwork_id", "source_url", name="uq_media_asset_artwork_source_url"),
    )
    op.create_index("ix_media_asset_artwork_id", "media_asset", ["artwork_id"])
    op.create_index("ix_media_asset_publication_state", "media_asset", ["publication_state"])
    op.create_table(
        "rights_evidence",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("source_record_id", postgresql.UUID(as_uuid=True)),
        sa.Column("media_asset_id", postgresql.UUID(as_uuid=True)),
        sa.Column("asserted_status", sa.String(64), nullable=False),
        sa.Column("license_uri", sa.Text()),
        sa.Column("evidence_field", sa.String(255), nullable=False),
        sa.Column("evidence_value", sa.Text()),
        sa.Column("evidence_url", sa.Text(), nullable=False),
        sa.Column("policy_version", sa.String(64), nullable=False),
        sa.Column("is_conflicting", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column(
            "observed_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.CheckConstraint(
            "(source_record_id IS NOT NULL)::integer + (media_asset_id IS NOT NULL)::integer = 1",
            name="ck_rights_evidence_one_subject",
        ),
        sa.ForeignKeyConstraint(["source_record_id"], ["source_record.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["media_asset_id"], ["media_asset.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_rights_evidence_source_record_id", "rights_evidence", ["source_record_id"])
    op.create_index("ix_rights_evidence_media_asset_id", "rights_evidence", ["media_asset_id"])


def downgrade() -> None:
    op.drop_table("rights_evidence")
    op.drop_table("media_asset")
    op.drop_table("artwork")
    op.drop_table("source_record")
    op.drop_table("source_provider")
