from collections.abc import Generator

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.session import create_database_engine, create_session_factory
from app.providers.openai_explanation import OpenAIExplanationProvider
from app.services.artwork_explanation import ExplanationProvider


def get_catalog_session() -> Generator[Session, None, None]:
    """Open a database session only for catalog endpoints that need one."""
    session_factory = create_session_factory(create_database_engine())
    with session_factory() as session:
        yield session


def get_explanation_provider() -> ExplanationProvider:
    settings = get_settings()
    return OpenAIExplanationProvider(
        api_key=settings.openai_api_key,
        model=settings.openai_model,
    )


def get_ai_image_hosts() -> tuple[str, ...]:
    return get_settings().openai_image_hosts
