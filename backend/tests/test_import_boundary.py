from app.domain.imports import FACTUAL_ARTWORK_FIELDS, select_factual_artwork_metadata


def test_factual_allowlist_excludes_authored_prose() -> None:
    payload = {
        "title": "Example",
        "medium": "Oil on canvas",
        "description": "Authored curatorial prose",
        "wall_description": "More authored prose",
    }

    selected = select_factual_artwork_metadata(payload)

    assert selected == {"title": "Example", "medium": "Oil on canvas"}
    assert "description" not in FACTUAL_ARTWORK_FIELDS
