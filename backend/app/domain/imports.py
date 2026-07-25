from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from app.domain.rights import Cc0MediaRightsPolicy, MediaRightsCandidate, RightsClaim

# Authored descriptions and other provider prose are deliberately absent.
FACTUAL_ARTWORK_FIELDS = frozenset(
    {"title", "creator_display", "date_text", "medium", "culture", "department"}
)


def select_factual_artwork_metadata(payload: Mapping[str, Any]) -> dict[str, Any]:
    """Keep only provider-neutral factual fields approved for the initial catalog."""
    return {key: payload[key] for key in FACTUAL_ARTWORK_FIELDS if key in payload}


@dataclass(frozen=True, slots=True)
class ImportCandidate:
    """Ephemeral provider metadata evaluated before anything may be persisted."""

    external_id: str
    source_url: str
    source_facts: dict[str, Any]
    artwork_facts: dict[str, Any]
    media_rights: MediaRightsCandidate


@dataclass(frozen=True, slots=True)
class ApprovedImportCandidate:
    """The only candidate shape that a future persistence service may accept."""

    external_id: str
    source_url: str
    source_facts: dict[str, Any]
    artwork_facts: dict[str, Any]
    image_url: str
    rights_claims: tuple[RightsClaim, ...]


def approve_for_persistence(
    candidate: ImportCandidate, policy: Cc0MediaRightsPolicy
) -> ApprovedImportCandidate | None:
    """Return a persistable command only after the central policy approves it."""
    decision = policy.evaluate(candidate.media_rights)
    if not decision.accepted or not candidate.media_rights.image_url:
        return None
    return ApprovedImportCandidate(
        external_id=candidate.external_id,
        source_url=candidate.source_url,
        source_facts=candidate.source_facts,
        artwork_facts=candidate.artwork_facts,
        image_url=candidate.media_rights.image_url,
        rights_claims=candidate.media_rights.claims,
    )
