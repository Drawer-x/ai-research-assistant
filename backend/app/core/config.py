from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


BACKEND_DIR = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    app_name: str = "AI Research Assistant API"
    database_url: str = f"sqlite:///{(BACKEND_DIR / 'ai_research_assistant.db').as_posix()}"
    secret_key: str = "development-only-change-this-secret-key"
    access_token_expire_minutes: int = 1440
    upload_dir: str = "uploads"
    max_pdf_upload_bytes: int = 50 * 1024 * 1024
    algorithm: str = "HS256"
    ecnu_api_key: str | None = None
    ecnu_base_url: str = "https://chat.ecnu.edu.cn/open/api/v1"
    ecnu_chat_model: str = "ecnu-max"
    ecnu_embedding_model: str = "ecnu-embedding-small"
    ai_timeout_seconds: float = 60.0
    ai_max_prompt_chars: int = 20_000
    embedding_batch_size: int = 64
    embedding_max_input_chars: int = 8_000

    model_config = SettingsConfigDict(env_file=BACKEND_DIR / ".env", extra="ignore")

    @property
    def upload_path(self) -> Path:
        path = Path(self.upload_dir)
        return path if path.is_absolute() else BACKEND_DIR / path


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
