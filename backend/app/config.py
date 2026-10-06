from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parents[1]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=BACKEND_DIR / ".env", extra="ignore")

    app_env: str = "dev"
    database_url: str = ""
    groq_api_key: str = ""
    groq_model: str = ""
    hf_token: str = ""
    embedding_model: str = "BAAI/bge-small-en-v1.5"
    fernet_key: str = ""
    llm_cache_dir: str = str(BACKEND_DIR / ".cache" / "llm")
    mem0_api_key: str = ""
    demo_database_url: str = ""


@lru_cache
def get_settings() -> Settings:
    return Settings()
