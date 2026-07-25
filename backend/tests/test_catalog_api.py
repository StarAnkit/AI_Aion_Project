import uuid
from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.api.dependencies import get_catalog_session
from app.core.config import get_settings
from app.db import models
from app.db.session import create_database_engine
from app.domain.rights import CC0_LICENSE_URI
from app.main import app


def _database_session_or_skip() -> Generator[Session, None, None]:
    if not get_settings().database_url:
        pytest.skip("AI_AION_DATABASE_URL is not configured")
    engine = create_database_engine()
    connection = engine.connect()
    transaction = connection.begin()
    session = Session(bind=connection, autoflush=False, expire_on_commit=False)
    try:
        yield session
    finally:
        session.close()
        transaction.rollback()
        connection.close()
        engine.dispose()


@pytest.fixture
def catalog_client() -> Generator[tuple[TestClient, str], None, None]:
    for database_session in _database_session_or_skip():
        provider_code = f"api-fixture-{uuid.uuid4().hex}"
        provider = models.SourceProvider(
            code=provider_code,
            name="API fixture provider",
            base_url="https://example.test",
            rights_policy_version="test-v1",
            is_enabled=True,
        )
        database_session.add(provider)
        database_session.flush()
        approved_id = _seed_catalog_fixture(
            database_session, provider, "approved", "approved", "published", "CC0"
        )
        _seed_catalog_fixture(database_session, provider, "hidden", "approved", "hidden")
        _seed_catalog_fixture(
            database_session, provider, "other-rights", "approved", "hidden", "Other"
        )
        _seed_catalog_fixture(database_session, provider, "rejected", "rejected", "hidden")
        database_session.flush()

        app.dependency_overrides[get_catalog_session] = _session_override(database_session)
        try:
            with TestClient(app) as client:
                yield client, f"{provider_code}:{approved_id}"
        finally:
            app.dependency_overrides.clear()


def test_catalog_api_exposes_only_approved_cc0_artwork(
    catalog_client: tuple[TestClient, str],
) -> None:
    client, approved_public_id = catalog_client

    response = client.get(f"/api/v1/catalog/artworks/{approved_public_id}")

    assert response.status_code == 200
    body = response.json()
    assert body["public_id"] == approved_public_id
    assert body["license"] == {
        "status": "CC0",
        "license_uri": CC0_LICENSE_URI,
        "evidence_url": "https://example.test/rights",
    }
    assert {"raw_facts", "id", "description"}.isdisjoint(body)


@pytest.mark.parametrize("external_id", ["hidden", "other-rights", "rejected"])
def test_catalog_api_hides_non_public_candidates(
    catalog_client: tuple[TestClient, str], external_id: str
) -> None:
    client, approved_public_id = catalog_client
    provider_code, _ = approved_public_id.split(":", maxsplit=1)

    response = client.get(f"/api/v1/catalog/artworks/{provider_code}:{external_id}")

    assert response.status_code == 404


def test_catalog_list_excludes_non_public_candidates(
    catalog_client: tuple[TestClient, str],
) -> None:
    client, approved_public_id = catalog_client
    provider_code, _ = approved_public_id.split(":", maxsplit=1)

    response = client.get("/api/v1/catalog/artworks?limit=50&offset=0")

    assert response.status_code == 200
    public_ids = {item["public_id"] for item in response.json()["items"]}
    assert f"{provider_code}:hidden" not in public_ids
    assert f"{provider_code}:other-rights" not in public_ids
    assert f"{provider_code}:rejected" not in public_ids


def test_catalog_pagination_validation() -> None:
    response = TestClient(app).get("/api/v1/catalog/artworks?limit=0")

    assert response.status_code == 422


def _seed_catalog_fixture(
    session: Session,
    provider: models.SourceProvider,
    external_id: str,
    rights_status: str,
    publication_state: str,
    evidence_status: str = "CC0",
) -> str:
    source_record = models.SourceRecord(
        provider=provider,
        external_id=external_id,
        source_url=f"https://example.test/artworks/{external_id}",
        raw_facts={"title": f"Fixture {external_id}"},
        payload_sha256="a" * 64,
    )
    artwork = models.Artwork(source_record=source_record, title=f"Fixture {external_id}")
    media_asset = models.MediaAsset(
        artwork=artwork,
        source_url=f"https://example.test/images/{external_id}.jpg",
        rights_status=rights_status,
        license_uri=CC0_LICENSE_URI,
        publication_state=publication_state,
    )
    models.RightsEvidence(
        media_asset=media_asset,
        asserted_status=evidence_status,
        license_uri=CC0_LICENSE_URI,
        evidence_field="share_license_status",
        evidence_value=evidence_status,
        evidence_url="https://example.test/rights",
        policy_version="test-v1",
    )
    session.add(source_record)
    return external_id


def _session_override(session: Session):
    def override() -> Generator[Session, None, None]:
        yield session

    return override
