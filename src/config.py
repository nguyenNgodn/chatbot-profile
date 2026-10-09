from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

from dotenv import load_dotenv
import os

load_dotenv()


ROOT_DIR = Path(__file__).resolve().parent.parent


def _as_psycopg_url(url: str) -> str:
    if url.startswith("postgresql://") and "+" not in url.split("://", 1)[0]:
        return "postgresql+psycopg://" + url[len("postgresql://") :]
    return url


class Settings(BaseSettings):
    DATABASE_URL: str = os.getenv("DATABASE_URL")
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY")
    GEMINI_API_KEYS: str = os.getenv("GEMINI_API_KEYS")
    SECRET_KEY: str = "change-me"
    CORS_ORIGINS: str = "http://localhost:3000"

    model_config = SettingsConfigDict(
        env_file=str(ROOT_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @property
    def database_url(self) -> str:
        return _as_psycopg_url(self.DATABASE_URL)

    @property
    def gemini_keys(self) -> list[str]:
        keys: list[str] = []
        for raw in (self.GEMINI_API_KEYS, self.GEMINI_API_KEY):
            for part in raw.split(","):
                key = part.strip()
                if key and key not in keys:
                    keys.append(key)
        return keys

    @property
    def cors_origins(self) -> list[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]


settings = Settings()
