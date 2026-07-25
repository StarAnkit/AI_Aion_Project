from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_prefix="AI_AION_", extra="ignore")
    app_name: str = "AI Aion API"
    environment: str = "development"
    api_v1_prefix: str = "/api/v1"
    cors_origins: tuple[str, ...] = ("http://localhost:5173",)


@lru_cache
def get_settings() -> Settings:
    return Settings()
