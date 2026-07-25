import uuid

import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.models import Artwork, MediaAsset, RightsEvidence, SourceProvider, SourceRecord
from app.db.session import create_database_engine
from app.domain.imports import ApprovedImportCandidate
from app.domain.rights import CC0_LICENSE_URI, Cc0MediaRightsPolicy, RightsClaim
from app.services.catalog_import import CatalogImportService, ProviderRegistration


def database_engine_or_skip():
    if not get_settings().database_url:
        pytest.skip("AI_AION_DATABASE_URL is not configured")
    return create_database_engine()


def approved_candidate(external_id: str) -> ApprovedImportCandidate:
    claim = RightsClaim(
        status="CC0",
        license_uri=CC0_LICENSE_URI,
        evidence_field="provider_rights_status",
        evidence_value="CC0",
    )
    return ApprovedImportCandidate(
        external_id=external_id,
        source_url=f"https://example.test/art/{external_id}",
        source_facts={"id": external_id, "share_license_status": "CC0"},
        artwork_facts={"title": "Integration fixture"},
        image_url=f"https://images.example.test/{external_id}.jpg",
        rights_claims=(claim,),
    )


def registration(code: str) -> ProviderRegistration:
    return ProviderRegistration(
        code=code,
        name="Integration fixture provider",
        base_url="https://example.test",
        rights_policy_version="test-v1",
        rights_evidence_url="https://example.test/rights",
    )


def test_service_persists_only_once_with_provenance_and_cc0_guard() -> None:
    engine = database_engine_or_skip()
    provider_code = f"integration-import-{uuid.uuid4()}"
    service = CatalogImportService(Cc0MediaRightsPolicy())

    try:
        with engine.connect() as connection:
            transaction = connection.begin()
            session = Session(bind=connection)
            try:
                first = service.persist_approved_candidates(
                    session, registration(provider_code), [approved_candidate("fixture-1")]
                )
                second = service.persist_approved_candidates(
                    session, registration(provider_code), [approved_candidate("fixture-1")]
                )

                assert (first.created, first.unchanged, first.processed) == (1, 0, 1)
                assert (second.created, second.unchanged, second.processed) == (0, 1, 1)
                provider = session.scalar(
                    select(SourceProvider).where(SourceProvider.code == provider_code)
                )
                assert provider is not None
                source_record = session.scalar(
                    select(SourceRecord).where(SourceRecord.provider_id == provider.id)
                )
                assert source_record is not None
                artwork = session.scalar(
                    select(Artwork).where(Artwork.source_record_id == source_record.id)
                )
                assert artwork is not None
                media_asset = session.scalar(
                    select(MediaAsset).where(MediaAsset.artwork_id == artwork.id)
                )
                assert media_asset is not None
                assert (
                    session.scalar(
                        select(RightsEvidence).where(
                            RightsEvidence.media_asset_id == media_asset.id
                        )
                    )
                    is not None
                )
            finally:
                session.close()
                transaction.rollback()
    finally:
        engine.dispose()


def test_service_rechecks_policy_before_any_provider_persistence() -> None:
    engine = database_engine_or_skip()
    provider_code = f"integration-rejected-{uuid.uuid4()}"
    service = CatalogImportService(Cc0MediaRightsPolicy())
    rejected = approved_candidate("rejected-fixture")
    rejected = ApprovedImportCandidate(
        external_id=rejected.external_id,
        source_url=rejected.source_url,
        source_facts=rejected.source_facts,
        artwork_facts=rejected.artwork_facts,
        image_url=rejected.image_url,
        rights_claims=(
            RightsClaim(
                status="Copyrighted",
                license_uri=None,
                evidence_field="provider_rights_status",
                evidence_value="Copyrighted",
            ),
        ),
    )

    try:
        with engine.connect() as connection:
            transaction = connection.begin()
            session = Session(bind=connection)
            try:
                summary = service.persist_approved_candidates(
                    session, registration(provider_code), [rejected]
                )

                assert summary.created == 0
                assert summary.skipped_by_reason == {"policy_copyrighted": 1}
                assert (
                    session.scalar(
                        select(SourceProvider).where(SourceProvider.code == provider_code)
                    )
                    is None
                )
            finally:
                session.close()
                transaction.rollback()
    finally:
        engine.dispose()
