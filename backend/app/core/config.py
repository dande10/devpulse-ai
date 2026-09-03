from functools import lru_cache

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str = "postgresql+psycopg://postgres:postgres@localhost:5432/devpulse"
    tavily_api_key: str | None = None
    cors_origins: str = "http://localhost:5173"
    tavily_max_results: int = 10
    tavily_timeout_seconds: float = 8.0
    tavily_retries: int = 2
    user_refresh_cooldown_seconds: int = 300

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    @field_validator("cors_origins")
    @classmethod
    def clean_origins(cls, value: str) -> str:
        return value

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
