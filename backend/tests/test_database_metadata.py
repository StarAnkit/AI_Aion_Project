from app.db import models  # noqa: F401
from app.db.base import Base


def test_initial_schema_has_only_approved_catalog_tables() -> None:
    assert set(Base.metadata.tables) == {
        "source_provider",
        "source_record",
        "artwork",
        "media_asset",
        "rights_evidence",
    }


def test_artwork_has_no_authored_description_column() -> None:
    assert "description" not in Base.metadata.tables["artwork"].columns
