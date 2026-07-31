from typing import Literal

from pydantic import BaseModel, Field, HttpUrl

from app.schemas.catalog import CatalogLicense


class MuseumFact(BaseModel):
    label: str
    value: str


class ExplanationProvenance(BaseModel):
    provider_name: str
    source_url: HttpUrl
    license: CatalogLicense


class GeneratedExplanation(BaseModel):
    summary: str = Field(max_length=1800)
    visual_observations: list[str] = Field(default_factory=list, max_length=8)
    inferences: list[str] = Field(default_factory=list, max_length=6)
    uncertainty: str = Field(max_length=800)
    insufficient_context: bool = False


class ArtworkExplanationResponse(BaseModel):
    status: Literal["ready", "insufficient_context", "not_configured"]
    ai_generated: bool
    content_notice: str
    rights_notice: str
    verified_museum_facts: list[MuseumFact] = Field(default_factory=list)
    generated: GeneratedExplanation | None = None
    provenance: ExplanationProvenance
    message: str | None = None
