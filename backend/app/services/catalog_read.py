from collections.abc import Sequence

from sqlalchemy import exists, func, select
from sqlalchemy.orm import Session, selectinload

from app.db.models import Artwork, MediaAsset, RightsEvidence, SourceProvider, SourceRecord
from app.domain.rights import (
    CC0_LICENSE_URI,
    Cc0MediaRightsPolicy,
    MediaRightsCandidate,
    RightsClaim,
)
from app.schemas.catalog import CatalogArtwork, CatalogLicense


class CatalogReadService:
    """Read public catalog data only after checking the shared CC0 policy again."""

    def __init__(self, policy: Cc0MediaRightsPolicy) -> None:
        self._policy = policy

    def list_artworks(
        self, session: Session, *, limit: int, offset: int
    ) -> tuple[list[CatalogArtwork], int]:
        statement = self._public_media_statement().order_by(MediaAsset.created_at, MediaAsset.id)
        media_assets = session.scalars(
            statement.options(selectinload(MediaAsset.rights_evidence)).limit(limit).offset(offset)
        ).all()
        total_statement = select(func.count()).select_from(
            self._public_media_statement().subquery()
        )
        total = session.scalar(total_statement) or 0
        return self._serialize_public_media(media_assets), total

    def get_artwork(self, session: Session, public_id: str) -> CatalogArtwork | None:
        provider_code, external_id = _parse_public_id(public_id)
        if provider_code is None:
            return None
        statement = self._public_media_statement().where(
            SourceProvider.code == provider_code,
            SourceRecord.external_id == external_id,
        )
        media_asset = session.scalar(statement.options(selectinload(MediaAsset.rights_evidence)))
        return self._serialize_media(media_asset) if media_asset is not None else None

    @staticmethod
    def _public_media_statement():
        approved_evidence = exists(
            select(1).where(
                RightsEvidence.media_asset_id == MediaAsset.id,
                RightsEvidence.asserted_status == "CC0",
                RightsEvidence.license_uri == CC0_LICENSE_URI,
                RightsEvidence.is_conflicting.is_(False),
            )
        )
        conflicting_evidence = exists(
            select(1).where(
                RightsEvidence.media_asset_id == MediaAsset.id,
                (RightsEvidence.is_conflicting.is_(True))
                | (RightsEvidence.asserted_status != "CC0")
                | (RightsEvidence.license_uri.is_distinct_from(CC0_LICENSE_URI)),
            )
        )
        return (
            select(MediaAsset)
            .join(MediaAsset.artwork)
            .join(Artwork.source_record)
            .join(SourceRecord.provider)
            .where(
                SourceProvider.is_enabled.is_(True),
                MediaAsset.media_type == "image",
                MediaAsset.publication_state == "published",
                MediaAsset.rights_status == "approved",
                MediaAsset.license_uri == CC0_LICENSE_URI,
                approved_evidence,
                ~conflicting_evidence,
            )
        )

    def _serialize_public_media(self, media_assets: Sequence[MediaAsset]) -> list[CatalogArtwork]:
        return [
            result for media_asset in media_assets if (result := self._serialize_media(media_asset))
        ]

    def _serialize_media(self, media_asset: MediaAsset) -> CatalogArtwork | None:
        evidence = tuple(media_asset.rights_evidence)
        claims = tuple(
            RightsClaim(
                item.asserted_status,
                item.license_uri,
                item.evidence_field,
                item.evidence_value,
            )
            for item in evidence
        )
        decision = self._policy.evaluate(MediaRightsCandidate(media_asset.source_url, claims))
        if not decision.accepted or any(item.is_conflicting for item in evidence):
            return None

        artwork = media_asset.artwork
        source_record = artwork.source_record
        provider = source_record.provider
        cc0_evidence = next(
            (
                item
                for item in evidence
                if item.asserted_status == "CC0"
                and item.license_uri == CC0_LICENSE_URI
                and not item.is_conflicting
            ),
            None,
        )
        if cc0_evidence is None:
            return None
        return CatalogArtwork(
            public_id=f"{provider.code}:{source_record.external_id}",
            title=artwork.title,
            creator_display=artwork.creator_display,
            date_text=artwork.date_text,
            medium=artwork.medium,
            culture=artwork.culture,
            department=artwork.department,
            image_url=media_asset.source_url,
            source_url=source_record.source_url,
            provider_code=provider.code,
            provider_name=provider.name,
            license=CatalogLicense(
                status=cc0_evidence.asserted_status,
                license_uri=cc0_evidence.license_uri,
                evidence_url=cc0_evidence.evidence_url,
            ),
        )


def _parse_public_id(public_id: str) -> tuple[str | None, str | None]:
    provider_code, separator, external_id = public_id.partition(":")
    if not separator or not provider_code or not external_id:
        return None, None
    return provider_code, external_id
