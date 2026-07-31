from dataclasses import dataclass
from typing import Protocol
from urllib.parse import urlparse

from app.schemas.catalog import CatalogArtwork
from app.schemas.explanation import (
    ArtworkExplanationResponse,
    ExplanationProvenance,
    GeneratedExplanation,
    MuseumFact,
)


@dataclass(frozen=True)
class ApprovedArtworkInput:
    """The complete and deliberately small payload allowed to cross the AI boundary."""

    image_url: str
    title: str
    creator_display: str | None
    date_text: str | None
    medium: str | None
    culture: str | None
    department: str | None


class ExplanationProvider(Protocol):
    @property
    def is_configured(self) -> bool: ...

    def explain(self, artwork: ApprovedArtworkInput) -> GeneratedExplanation: ...


class ArtworkExplanationService:
    def __init__(
        self, provider: ExplanationProvider, *, allowed_image_hosts: tuple[str, ...]
    ) -> None:
        self._provider = provider
        self._allowed_image_hosts = frozenset(allowed_image_hosts)

    def explain(self, artwork: CatalogArtwork) -> ArtworkExplanationResponse:
        facts = _verified_facts(artwork)
        provenance = ExplanationProvenance(
            provider_name=artwork.provider_name,
            source_url=artwork.source_url,
            license=artwork.license,
        )
        shared = {
            "content_notice": "AI-generated explanation; verify interpretations independently.",
            "rights_notice": (
                "CC0 applies to the approved artwork image, not to this AI-generated prose."
            ),
            "verified_museum_facts": facts,
            "provenance": provenance,
        }
        if not self._provider.is_configured:
            return ArtworkExplanationResponse(
                status="not_configured",
                ai_generated=False,
                generated=None,
                message="Artwork explanation is disabled until an OpenAI API key is configured.",
                **shared,
            )

        image_url = str(artwork.image_url)
        parsed_image_url = urlparse(image_url)
        if (
            artwork.provider_code != "cleveland"
            or parsed_image_url.scheme != "https"
            or parsed_image_url.hostname not in self._allowed_image_hosts
            or parsed_image_url.username is not None
            or parsed_image_url.password is not None
        ):
            raise ValueError("Approved artwork image URL is not on the AI image host allowlist")

        generated = self._provider.explain(
            ApprovedArtworkInput(
                image_url=image_url,
                title=artwork.title,
                creator_display=artwork.creator_display,
                date_text=artwork.date_text,
                medium=artwork.medium,
                culture=artwork.culture,
                department=artwork.department,
            )
        )
        return ArtworkExplanationResponse(
            status="insufficient_context" if generated.insufficient_context else "ready",
            ai_generated=True,
            generated=generated,
            **shared,
        )


def _verified_facts(artwork: CatalogArtwork) -> list[MuseumFact]:
    values = (
        ("Title", artwork.title),
        ("Creator", artwork.creator_display),
        ("Date", artwork.date_text),
        ("Medium", artwork.medium),
        ("Culture", artwork.culture),
        ("Department", artwork.department),
    )
    return [MuseumFact(label=label, value=value) for label, value in values if value]
