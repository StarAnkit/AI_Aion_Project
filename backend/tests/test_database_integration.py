import uuid

import pytest
from sqlalchemy import inspect
from sqlalchemy.exc import IntegrityError

from app.core.config import get_settings
from app.db import models
from app.db.session import create_database_engine


def database_engine_or_skip():
    if not get_settings().database_url:
        pytest.skip("AI_AION_DATABASE_URL is not configured")
    return create_database_engine()


def test_migrated_database_has_expected_catalog_tables() -> None:
    engine = database_engine_or_skip()
    try:
        assert set(inspect(engine).get_table_names()) == {
            "alembic_version",
            "source_provider",
            "source_record",
            "artwork",
            "media_asset",
            "rights_evidence",
        }
    finally:
        engine.dispose()


def test_database_rejects_published_media_without_approved_cc0_rights() -> None:
    engine = database_engine_or_skip()
    provider_id = uuid.uuid4()
    source_record_id = uuid.uuid4()
    artwork_id = uuid.uuid4()

    try:
        with engine.connect() as connection:
            transaction = connection.begin()
            try:
                connection.execute(
                    models.SourceProvider.__table__.insert(),
                    {
                        "id": provider_id,
                        "code": f"integration-{provider_id}",
                        "name": "Integration fixture",
                        "base_url": "https://example.test",
                        "rights_policy_version": "test-v1",
                    },
                )
                connection.execute(
                    models.SourceRecord.__table__.insert(),
                    {
                        "id": source_record_id,
                        "provider_id": provider_id,
                        "external_id": "fixture-1",
                        "source_url": "https://example.test/artworks/fixture-1",
                        "raw_facts": {"title": "Fixture"},
                        "payload_sha256": "0" * 64,
                    },
                )
                connection.execute(
                    models.Artwork.__table__.insert(),
                    {
                        "id": artwork_id,
                        "source_record_id": source_record_id,
                        "title": "Fixture",
                    },
                )

                with pytest.raises(IntegrityError):
                    connection.execute(
                        models.MediaAsset.__table__.insert(),
                        {
                            "id": uuid.uuid4(),
                            "artwork_id": artwork_id,
                            "source_url": "https://example.test/images/fixture.jpg",
                            "rights_status": "pending",
                            "publication_state": "published",
                        },
                    )
            finally:
                transaction.rollback()
    finally:
        engine.dispose()
