from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


BACKEND_DIR = Path(__file__).resolve().parents[2]
ENV_FILE = BACKEND_DIR / ".env"


class Settings(BaseSettings):
    app_name: str = "Enterprise Data Reconciliation Engine"
    app_version: str = "1.0.0"
    debug: bool = True

    database_url: str

    model_config = SettingsConfigDict(
        env_file=ENV_FILE,
        extra="ignore"
    )


settings = Settings()

