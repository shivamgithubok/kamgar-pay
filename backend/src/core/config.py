from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


BACKEND_DIR = Path(__file__).resolve().parents[1]
DEFAULT_DATABASE_URL = f"sqlite:///{(BACKEND_DIR / 'labour_erp.db').resolve().as_posix()}"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    project_name: str = "Labour ERP API"
    api_v1_prefix: str = "/api/v1"
    database_url: str = Field(default=DEFAULT_DATABASE_URL)
    jwt_secret_key: str = Field(default="change-this-in-production", min_length=16)
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60

    @property
    def sqlite_connect_args(self) -> dict[str, bool]:
        if self.database_url.startswith("sqlite"):
            return {"check_same_thread": False}
        return {}


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
