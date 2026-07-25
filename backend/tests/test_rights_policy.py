import pytest

from app.domain.rights import (
    CC0_LICENSE_URI,
    Cc0MediaRightsPolicy,
    MediaRightsCandidate,
    RightsClaim,
    RightsDecisionReason,
)

IMAGE_URL = "https://images.example.test/artwork.jpg"


def claim(status: str | None, license_uri: str | None = CC0_LICENSE_URI) -> RightsClaim:
    return RightsClaim(
        status=status,
        license_uri=license_uri,
        evidence_field="provider_rights_status",
        evidence_value=status,
    )


@pytest.mark.parametrize(
    ("candidate", "reason"),
    [
        (MediaRightsCandidate(IMAGE_URL, ()), RightsDecisionReason.MISSING_RIGHTS),
        (
            MediaRightsCandidate(IMAGE_URL, (claim("Copyrighted", None),)),
            RightsDecisionReason.COPYRIGHTED,
        ),
        (
            MediaRightsCandidate(IMAGE_URL, (claim("Other", None),)),
            RightsDecisionReason.OTHER_RIGHTS,
        ),
        (
            MediaRightsCandidate(IMAGE_URL, (claim("CC0"), claim("Copyrighted", None))),
            RightsDecisionReason.CONFLICTING_EVIDENCE,
        ),
        (MediaRightsCandidate(None, (claim("CC0"),)), RightsDecisionReason.MISSING_IMAGE),
    ],
)
def test_policy_rejects_unsafe_candidates(
    candidate: MediaRightsCandidate, reason: RightsDecisionReason
) -> None:
    decision = Cc0MediaRightsPolicy().evaluate(candidate)

    assert decision.accepted is False
    assert decision.reason is reason


def test_policy_accepts_explicit_cc0_image() -> None:
    decision = Cc0MediaRightsPolicy().evaluate(MediaRightsCandidate(IMAGE_URL, (claim("CC0"),)))

    assert decision.accepted is True
    assert decision.reason is RightsDecisionReason.ACCEPTED
