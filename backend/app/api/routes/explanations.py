from collections import defaultdict, deque
from threading import Lock
from time import monotonic
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_ai_image_hosts, get_catalog_session, get_explanation_provider
from app.domain.rights import Cc0MediaRightsPolicy
from app.schemas.explanation import ArtworkExplanationResponse
from app.services.artwork_explanation import ArtworkExplanationService, ExplanationProvider
from app.services.catalog_read import CatalogReadService

router = APIRouter(prefix="/catalog/artworks", tags=["artwork explanations"])
CatalogSession = Annotated[Session, Depends(get_catalog_session)]
Provider = Annotated[ExplanationProvider, Depends(get_explanation_provider)]
ImageHosts = Annotated[tuple[str, ...], Depends(get_ai_image_hosts)]
_request_times: dict[str, deque[float]] = defaultdict(deque)
_global_request_times: deque[float] = deque()
_rate_lock = Lock()
_RATE_WINDOW_SECONDS = 60
_RATE_LIMIT = 5
_GLOBAL_RATE_LIMIT = 30


@router.post(
    "/{public_id}/explanation",
    response_model=ArtworkExplanationResponse,
    summary="Explain one publicly approved CC0 artwork",
)
def explain_artwork(
    public_id: str,
    request: Request,
    session: CatalogSession,
    provider: Provider,
    image_hosts: ImageHosts,
) -> ArtworkExplanationResponse:
    if request.headers.get("content-length") not in (None, "0"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Explanation requests do not accept a request body",
        )
    artwork = CatalogReadService(Cc0MediaRightsPolicy()).get_artwork(session, public_id)
    if artwork is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Catalog artwork not found"
        )
    _enforce_local_rate_limit(request)
    try:
        return ArtworkExplanationService(provider, allowed_image_hosts=image_hosts).explain(artwork)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Artwork explanation is temporarily unavailable",
        ) from exc


def _enforce_local_rate_limit(request: Request) -> None:
    """Small single-process guard; production still needs an edge/distributed quota."""
    client = request.client.host if request.client else "unknown"
    now = monotonic()
    with _rate_lock:
        while _global_request_times and now - _global_request_times[0] >= _RATE_WINDOW_SECONDS:
            _global_request_times.popleft()
        if len(_global_request_times) >= _GLOBAL_RATE_LIMIT:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Explanation capacity reached; try again later",
            )
        timestamps = _request_times[client]
        while timestamps and now - timestamps[0] >= _RATE_WINDOW_SECONDS:
            timestamps.popleft()
        if len(timestamps) >= _RATE_LIMIT:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many explanation requests; try again later",
            )
        timestamps.append(now)
        _global_request_times.append(now)
        for key in tuple(_request_times):
            if not _request_times[key] or now - _request_times[key][-1] >= _RATE_WINDOW_SECONDS:
                del _request_times[key]
