from dataclasses import dataclass
from enum import StrEnum

CC0_LICENSE_URI = "https://creativecommons.org/publicdomain/zero/1.0/"


class RightsDecisionReason(StrEnum):
    ACCEPTED = "accepted"
    MISSING_IMAGE = "missing_image"
    MISSING_RIGHTS = "missing_rights"
    COPYRIGHTED = "copyrighted"
    OTHER_RIGHTS = "other_rights"
    CONFLICTING_EVIDENCE = "conflicting_evidence"


@dataclass(frozen=True, slots=True)
class RightsClaim:
    status: str | None
    license_uri: str | None
    evidence_field: str
    evidence_value: str | None


@dataclass(frozen=True, slots=True)
class MediaRightsCandidate:
    image_url: str | None
    claims: tuple[RightsClaim, ...]


@dataclass(frozen=True, slots=True)
class RightsDecision:
    accepted: bool
    reason: RightsDecisionReason


class Cc0MediaRightsPolicy:
    """Fail-closed publication policy shared by every future provider adapter."""

    def evaluate(self, candidate: MediaRightsCandidate) -> RightsDecision:
        if not candidate.image_url or not candidate.image_url.strip():
            return RightsDecision(False, RightsDecisionReason.MISSING_IMAGE)
        if not candidate.claims:
            return RightsDecision(False, RightsDecisionReason.MISSING_RIGHTS)

        normalized = {
            ((claim.status or "").strip().casefold(), (claim.license_uri or "").strip())
            for claim in candidate.claims
        }
        if len(normalized) > 1:
            return RightsDecision(False, RightsDecisionReason.CONFLICTING_EVIDENCE)

        status, license_uri = normalized.pop()
        if not status:
            return RightsDecision(False, RightsDecisionReason.MISSING_RIGHTS)
        if status == "copyrighted":
            return RightsDecision(False, RightsDecisionReason.COPYRIGHTED)
        if status != "cc0":
            return RightsDecision(False, RightsDecisionReason.OTHER_RIGHTS)
        if not license_uri:
            return RightsDecision(False, RightsDecisionReason.MISSING_RIGHTS)
        if license_uri != CC0_LICENSE_URI:
            return RightsDecision(False, RightsDecisionReason.OTHER_RIGHTS)
        return RightsDecision(True, RightsDecisionReason.ACCEPTED)
