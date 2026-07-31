from dataclasses import fields

import pytest

from app.domain.rights import CC0_LICENSE_URI
from app.schemas.catalog import CatalogArtwork, CatalogLicense
from app.schemas.explanation import GeneratedExplanation
from app.services.artwork_explanation import ApprovedArtworkInput, ArtworkExplanationService


class FakeProvider:
    def __init__(self, *, configured: bool = True, insufficient: bool = False) -> None:
        self.is_configured = configured
        self.insufficient = insufficient
        self.received: ApprovedArtworkInput | None = None

    def explain(self, artwork: ApprovedArtworkInput) -> GeneratedExplanation:
        self.received = artwork
        return GeneratedExplanation(
            summary="A limited explanation.",
            visual_observations=["A blue area is visible."],
            inferences=[],
            uncertainty="The depicted identity cannot be verified.",
            insufficient_context=self.insufficient,
        )


def artwork(image_url: str = "https://openaccess-cdn.clevelandart.org/image.jpg") -> CatalogArtwork:
    return CatalogArtwork(
        public_id="cleveland:123",
        title="Approved work",
        creator_display="Museum creator value",
        date_text=None,
        medium="Oil",
        culture=None,
        department="Paintings",
        image_url=image_url,
        source_url="https://www.clevelandart.org/art/123",
        provider_code="cleveland",
        provider_name="Cleveland Museum of Art",
        license=CatalogLicense(
            status="CC0",
            license_uri=CC0_LICENSE_URI,
            evidence_url="https://www.clevelandart.org/open-access",
        ),
    )


def test_provider_receives_only_allowlisted_normalized_input() -> None:
    provider = FakeProvider()
    result = ArtworkExplanationService(
        provider, allowed_image_hosts=("openaccess-cdn.clevelandart.org",)
    ).explain(artwork())

    assert result.status == "ready"
    assert result.ai_generated is True
    assert provider.received is not None
    assert {field.name for field in fields(provider.received)} == {
        "image_url", "title", "creator_display", "date_text", "medium", "culture", "department"
    }
    assert "CC0 applies to the approved artwork image" in result.rights_notice
    assert str(result.provenance.license.license_uri) == CC0_LICENSE_URI


@pytest.mark.parametrize(
    "url",
    [
        "http://openaccess-cdn.clevelandart.org/image.jpg",
        "https://evil.example/image.jpg",
        "https://user:pass@openaccess-cdn.clevelandart.org/image.jpg",
    ],
)
def test_provider_rejects_non_allowlisted_or_unsafe_image_urls(url: str) -> None:
    provider = FakeProvider()
    with pytest.raises(ValueError, match="allowlist"):
        ArtworkExplanationService(
            provider, allowed_image_hosts=("openaccess-cdn.clevelandart.org",)
        ).explain(artwork(url))
    assert provider.received is None


def test_missing_key_returns_disabled_state_without_provider_call() -> None:
    provider = FakeProvider(configured=False)
    result = ArtworkExplanationService(
        provider, allowed_image_hosts=("openaccess-cdn.clevelandart.org",)
    ).explain(artwork("https://evil.example/not-used.jpg"))
    assert result.status == "not_configured"
    assert result.ai_generated is False
    assert result.generated is None
    assert provider.received is None


def test_insufficient_context_is_explicit() -> None:
    result = ArtworkExplanationService(
        FakeProvider(insufficient=True),
        allowed_image_hosts=("openaccess-cdn.clevelandart.org",),
    ).explain(artwork())
    assert result.status == "insufficient_context"
    assert result.generated and result.generated.insufficient_context
