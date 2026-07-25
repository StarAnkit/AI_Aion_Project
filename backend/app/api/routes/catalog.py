from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_catalog_session
from app.domain.rights import Cc0MediaRightsPolicy
from app.schemas.catalog import CatalogArtwork, CatalogPage
from app.services.catalog_read import CatalogReadService

router = APIRouter(prefix="/catalog/artworks", tags=["catalog"])

CatalogSession = Annotated[Session, Depends(get_catalog_session)]


@router.get("", response_model=CatalogPage, summary="List publicly approved CC0 artworks")
def list_catalog_artworks(
    session: CatalogSession,
    limit: int = Query(default=20, ge=1, le=50),
    offset: int = Query(default=0, ge=0),
) -> CatalogPage:
    items, total = CatalogReadService(Cc0MediaRightsPolicy()).list_artworks(
        session, limit=limit, offset=offset
    )
    return CatalogPage(items=items, limit=limit, offset=offset, total=total)


@router.get(
    "/{public_id}", response_model=CatalogArtwork, summary="Get one publicly approved CC0 artwork"
)
def get_catalog_artwork(public_id: str, session: CatalogSession) -> CatalogArtwork:
    artwork = CatalogReadService(Cc0MediaRightsPolicy()).get_artwork(session, public_id)
    if artwork is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Catalog artwork not found"
        )
    return artwork
