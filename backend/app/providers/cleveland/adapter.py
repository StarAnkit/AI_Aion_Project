from collections.abc import AsyncIterator, Mapping
from typing import Any, Protocol

from app.domain.imports import ImportCandidate, select_factual_artwork_metadata
from app.domain.rights import CC0_LICENSE_URI, MediaRightsCandidate, RightsClaim

CLEVELAND_CODE = "cleveland"
CLEVELAND_ARTWORK_BASE_URL = "https://www.clevelandart.org/art"

# Source facts are conservative and never contain images or authored prose.
CLEVELAND_SOURCE_FACT_FIELDS = frozenset(
    {
        "id",
        "title",
        "creation_date",
        "technique",
        "culture",
        "department",
        "share_license_status",
    }
)


class ClevelandRecordSource(Protocol):
    """Metadata-only source; a future live implementation requires separate approval."""

    def fetch_records(self, *, limit: int) -> AsyncIterator[Mapping[str, Any]]: ...


class ClevelandProviderAdapter:
    code = CLEVELAND_CODE

    def __init__(self, source: ClevelandRecordSource) -> None:
        self._source = source

    async def discover(self, *, limit: int) -> AsyncIterator[ImportCandidate]:
        if limit < 1:
            raise ValueError("limit must be positive")
        async for record in self._source.fetch_records(limit=limit):
            yield self.map_record(record)

    def map_record(self, record: Mapping[str, Any]) -> ImportCandidate:
        external_id = str(record.get("id") or "").strip()
        source_url = str(record.get("url") or "").strip()
        if not source_url and external_id:
            source_url = f"{CLEVELAND_ARTWORK_BASE_URL}/{external_id}"

        return ImportCandidate(
            external_id=external_id,
            source_url=source_url,
            source_facts={
                key: record[key] for key in CLEVELAND_SOURCE_FACT_FIELDS if key in record
            },
            artwork_facts=select_factual_artwork_metadata(self._map_artwork_facts(record)),
            media_rights=MediaRightsCandidate(
                image_url=self._image_url(record),
                claims=self._rights_claims(record.get("share_license_status")),
            ),
        )

    @staticmethod
    def _map_artwork_facts(record: Mapping[str, Any]) -> dict[str, Any]:
        creators = record.get("creators")
        creator_display = None
        if isinstance(creators, list) and creators and isinstance(creators[0], Mapping):
            creator_display = creators[0].get("description")

        culture = record.get("culture")
        if isinstance(culture, list):
            culture = ", ".join(str(value) for value in culture if value)

        return {
            "title": record.get("title"),
            "creator_display": creator_display,
            "date_text": record.get("creation_date"),
            "medium": record.get("technique"),
            "culture": culture,
            "department": record.get("department"),
        }

    @staticmethod
    def _image_url(record: Mapping[str, Any]) -> str | None:
        images = record.get("images")
        if not isinstance(images, Mapping):
            return None
        web = images.get("web")
        if not isinstance(web, Mapping):
            return None
        url = web.get("url")
        return str(url).strip() if url else None

    @staticmethod
    def _rights_claims(status_value: Any) -> tuple[RightsClaim, ...]:
        # A list is treated as multiple claims so unexpected upstream conflicts fail closed.
        statuses = status_value if isinstance(status_value, list) else [status_value]
        claims: list[RightsClaim] = []
        for status in statuses:
            if status is None:
                continue
            normalized_status = str(status).strip()
            claims.append(
                RightsClaim(
                    status=normalized_status,
                    license_uri=(
                        CC0_LICENSE_URI if normalized_status.casefold() == "cc0" else None
                    ),
                    evidence_field="share_license_status",
                    evidence_value=normalized_status,
                )
            )
        return tuple(claims)
