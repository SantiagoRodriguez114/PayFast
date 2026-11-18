from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


PROJECT_ROOT = Path(__file__).resolve().parents[3]


class Settings(BaseSettings):
    database_url: str

    secret_key: str  # clave privada para la generación de tokens JWT
    algorithm: str = "HS256" # algoritmo para la generación de tokens JWT
    access_token_expire_minutes: int = 30 # tiempo de validez del token

    enable_demo_topups: bool = False

    frontend_origin: str = ""

    model_config = SettingsConfigDict(
        env_file=PROJECT_ROOT / ".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )


settings = Settings()