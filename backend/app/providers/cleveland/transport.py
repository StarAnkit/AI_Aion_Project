from collections.abc import AsyncIterator, Mapping
from typing import Any

import httpx

CLEVELAND_API_BASE_URL = "https://openaccess-api.clevelandart.org"
MAX_METADATA_RECORDS_PER_REQUEST = 100


class ClevelandApiMetadataSource:
    """Fetch Cleveland JSON metadata only; never request image asset URLs."""

    def __init__(
        self,
        client: httpx.AsyncClient,
        *,
        filters: Mapping[str, str] | None = None,
    ) -> None:
        self._client = client
        self._filters = dict(filters or {})

    async def fetch_records(self, *, limit: int) -> AsyncIterator[Mapping[str, Any]]:
        if not 1 <= limit <= MAX_METADATA_RECORDS_PER_REQUEST:
            raise ValueError(f"limit must be between 1 and {MAX_METADATA_RECORDS_PER_REQUEST}")

        response = await self._client.get(
            "/api/artworks/",
            params={"limit": str(limit), "skip": "0", **self._filters},
            headers={"Accept": "application/json"},
        )
        response.raise_for_status()
        payload = response.json()
        records = payload.get("data") if isinstance(payload, Mapping) else None
        if not isinstance(records, list):
            raise ValueError("Cleveland API response does not contain a data list")

        for record in records[:limit]:
            if not isinstance(record, Mapping):
                raise ValueError("Cleveland API returned a non-object artwork record")
            yield record
