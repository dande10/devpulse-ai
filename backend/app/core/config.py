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

    # Email notifications for feedback and technology requests. All optional —
    # notifications are silently skipped (just logged) until these are set,
    # so the feature works today and starts actually emailing the moment
    # real SMTP credentials and a destination address are added.
    smtp_host: str | None = None
    smtp_port: int = 587
    smtp_user: str | None = None
    smtp_password: str | None = None
    smtp_from_email: str | None = None
    notify_email: str | None = None

    # Shared-secret header required on every /api/admin/* route (see
    # app/api/admin_auth.py). Unset means those routes reject every request —
    # there is no "admin mode without a token" fallback.
    admin_token: str | None = None

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    @field_validator("cors_origins")
    @classmethod
    def clean_origins(cls, value: str) -> str:
        return value

    @field_validator("database_url")
    @classmethod
    def use_psycopg_driver(cls, value: str) -> str:
        """Normalize managed-Postgres connection strings (e.g. Render's
        "postgres://..." / "postgresql://...") to the psycopg3 driver this
        app is built on, so a hosting provider's raw connection string works
        without hand-editing."""
        if value.startswith("postgres://"):
            return "postgresql+psycopg://" + value[len("postgres://") :]
        if value.startswith("postgresql://"):
            return "postgresql+psycopg://" + value[len("postgresql://") :]
        return value

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
