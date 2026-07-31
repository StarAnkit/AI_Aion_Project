from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_prefix="AI_AION_", extra="ignore")
    app_name: str = "AI Aion API"
    environment: str = "development"
    api_v1_prefix: str = "/api/v1"
    cors_origins: tuple[str, ...] = ("http://localhost:5173",)
    database_url: str | None = None
    openai_api_key: str | None = None
    openai_model: str = "gpt-5.6"
    openai_image_hosts: tuple[str, ...] = ("openaccess-cdn.clevelandart.org",)

    def require_database_url(self) -> str:
        """Return the database URL only when a database feature needs it."""
        if not self.database_url:
            raise RuntimeError("AI_AION_DATABASE_URL must be set before using database features")
        return self.database_url


@lru_cache
def get_settings() -> Settings:
    return Settings()
