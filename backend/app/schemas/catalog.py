from pydantic import BaseModel, Field, HttpUrl


class CatalogLicense(BaseModel):
    status: str = Field(examples=["CC0"])
    license_uri: HttpUrl
    evidence_url: HttpUrl


class CatalogArtwork(BaseModel):
    """Public, factual representation of one rights-approved image asset."""

    public_id: str
    title: str
    creator_display: str | None
    date_text: str | None
    medium: str | None
    culture: str | None
    department: str | None
    image_url: HttpUrl
    source_url: HttpUrl
    provider_code: str
    provider_name: str
    license: CatalogLicense


class CatalogPage(BaseModel):
    items: list[CatalogArtwork]
    limit: int = Field(ge=1, le=50)
    offset: int = Field(ge=0)
    total: int = Field(ge=0)
