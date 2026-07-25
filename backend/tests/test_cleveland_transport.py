import asyncio

import httpx
import pytest

from app.providers.cleveland.transport import ClevelandApiMetadataSource


def test_transport_requests_only_capped_artwork_metadata() -> None:
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return httpx.Response(
            200,
            json={
                "data": [
                    {
                        "id": 900001,
                        "title": "Synthetic metadata response",
                        "share_license_status": "CC0",
                        "images": {"web": {"url": "https://images.example.test/900001.jpg"}},
                    }
                ]
            },
        )

    async def fetch() -> list[object]:
        async with httpx.AsyncClient(
            base_url="https://openaccess-api.clevelandart.org",
            transport=httpx.MockTransport(handler),
        ) as client:
            source = ClevelandApiMetadataSource(client, filters={"cc0": "", "has_image": "1"})
            return [record async for record in source.fetch_records(limit=1)]

    records = asyncio.run(fetch())

    assert len(records) == 1
    assert len(requests) == 1
    assert requests[0].url.path == "/api/artworks/"
    assert requests[0].url.params["limit"] == "1"
    assert requests[0].url.params["cc0"] == ""


def test_transport_rejects_an_uncapped_request_before_http() -> None:
    async def fetch() -> None:
        async with httpx.AsyncClient(
            base_url="https://openaccess-api.clevelandart.org",
            transport=httpx.MockTransport(
                lambda request: pytest.fail(f"unexpected request: {request.url}")
            ),
        ) as client:
            source = ClevelandApiMetadataSource(client)
            _ = [record async for record in source.fetch_records(limit=101)]

    with pytest.raises(ValueError, match="between 1 and 100"):
        asyncio.run(fetch())
