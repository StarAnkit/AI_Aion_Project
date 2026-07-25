import asyncio
import json
from collections.abc import AsyncIterator, Mapping
from pathlib import Path
from typing import Any

import pytest

from app.domain.imports import ImportCandidate, approve_for_persistence
from app.domain.rights import Cc0MediaRightsPolicy, RightsDecisionReason
from app.providers.cleveland.adapter import ClevelandProviderAdapter

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "cleveland_records.synthetic.json"


def load_fixture_records() -> list[dict[str, Any]]:
    return json.loads(FIXTURE_PATH.read_text())


def records_by_scenario() -> dict[str, dict[str, Any]]:
    return {record["_fixture_scenario"]: record for record in load_fixture_records()}


class FixtureClevelandSource:
    """In-memory metadata source; it performs no network or image operations."""

    def __init__(self, records: list[dict[str, Any]]) -> None:
        self._records = records

    async def fetch_records(self, *, limit: int) -> AsyncIterator[Mapping[str, Any]]:
        for record in self._records[:limit]:
            yield record


@pytest.mark.parametrize(
    ("scenario", "reason"),
    [
        ("missing_rights", RightsDecisionReason.MISSING_RIGHTS),
        ("copyrighted", RightsDecisionReason.COPYRIGHTED),
        ("other_rights", RightsDecisionReason.OTHER_RIGHTS),
        ("conflicting_rights", RightsDecisionReason.CONFLICTING_EVIDENCE),
        ("missing_image", RightsDecisionReason.MISSING_IMAGE),
    ],
)
def test_rejected_fixture_never_becomes_persistable(
    scenario: str, reason: RightsDecisionReason
) -> None:
    record = records_by_scenario()[scenario]
    adapter = ClevelandProviderAdapter(FixtureClevelandSource([]))
    candidate = adapter.map_record(record)
    policy = Cc0MediaRightsPolicy()

    assert policy.evaluate(candidate.media_rights).reason is reason
    assert approve_for_persistence(candidate, policy) is None
    assert "images" not in candidate.source_facts
    assert "url" not in candidate.source_facts


def test_explicit_cc0_fixture_becomes_provider_neutral_persistable_candidate() -> None:
    record = records_by_scenario()["accepted_cc0"]
    adapter = ClevelandProviderAdapter(FixtureClevelandSource([]))
    candidate = adapter.map_record(record)

    approved = approve_for_persistence(candidate, Cc0MediaRightsPolicy())

    assert isinstance(candidate, ImportCandidate)
    assert approved is not None
    assert approved.external_id == "900001"
    assert approved.image_url == "https://images.example.test/900001.jpg"
    assert approved.artwork_facts == {
        "title": "Synthetic Blue Vessel",
        "creator_display": "Synthetic Maker",
        "date_text": "circa 1900",
        "medium": "Synthetic glazed ceramic",
        "culture": "Synthetic culture",
        "department": "Test collection",
    }
    assert "description" not in candidate.source_facts
    assert "tombstone" not in candidate.source_facts
    assert "images" not in candidate.source_facts


def test_adapter_discovers_only_from_injected_fixture_source_and_honors_limit() -> None:
    source = FixtureClevelandSource(load_fixture_records())
    adapter = ClevelandProviderAdapter(source)

    async def collect() -> list[ImportCandidate]:
        return [candidate async for candidate in adapter.discover(limit=2)]

    candidates = asyncio.run(collect())

    assert len(candidates) == 2
    assert all(isinstance(candidate, ImportCandidate) for candidate in candidates)
