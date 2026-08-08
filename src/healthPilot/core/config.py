from functools import lru_cache
from typing import List
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


def normalize_database_url(url: str) -> str:
    """
    Convert standard PostgreSQL URLs (e.g. from Neon) to SQLAlchemy asyncpg form.
    """
    if url.startswith("postgres://"):
        url = f"postgresql+asyncpg://{url[len('postgres://'):]}"
    elif url.startswith("postgresql://") and not url.startswith("postgresql+"):
        url = f"postgresql+asyncpg://{url[len('postgresql://'):]}"

    parsed = urlparse(url)
    query = dict(parse_qsl(parsed.query, keep_blank_values=True))

    # asyncpg uses ssl=, not sslmode=
    if "sslmode" in query and "ssl" not in query:
        sslmode = query.pop("sslmode")
        if sslmode in {"require", "verify-ca", "verify-full"}:
            query["ssl"] = "require"
        elif sslmode == "prefer":
            query["ssl"] = "prefer"

    # Not supported by asyncpg via URL
    query.pop("channel_binding", None)

    return urlunparse(parsed._replace(query=urlencode(query)))


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        case_sensitive=True,
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Project settings
    PROJECT_NAME: str = "HealthPilot"
    PROJECT_DESCRIPTION: str = "An Agentic AI Lifestyle Recommendation System Backend API"
    VERSION: str = "0.1.0"
    API_V1_STR: str = "/api/v1"
    ALLOWED_ORIGINS: List[str] = ["*"]

    # API Settings
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000

    # Database (Neon PostgreSQL)
    DATABASE_URL: str = "postgresql+asyncpg://user:pass@localhost/healthpilot"

    # Session
    SESSION_SECRET: str = "change-me-in-production"
    SESSION_COOKIE_NAME: str = "healthpilot_session"
    SESSION_MAX_AGE: int = 60 * 60 * 24 * 7  # 7 days

    # Admin bootstrap
    ADMIN_EMAIL: str = ""
    ADMIN_PASSWORD: str = ""

    # Agent LLM (Mesh API / OpenAI-compatible)
    OPENAI_BASE_URL: str = "https://api.openai.com/v1"
    OPENAI_API_KEY: str = "sk-proj-your-key-here"
    LLM_MODEL: str = "gpt-4o"
    LLM_MODEL_PROVIDER: str = "openai"
    LLM_TEMPERATURE: float = 0.0

    # Embeddings (Mesh API — reuses OPENAI_BASE_URL + OPENAI_API_KEY)
    EMBEDDING_MODEL: str = "text-embedding-3-small"

    # Presidio (embedded)
    PRESIDIO_SCORE_THRESHOLD: float = 0.35
    PRESIDIO_SPACY_MODEL: str = "en_core_web_lg"

    # NeMo Guardrails (embedded)
    NEMO_CONFIG_PATH: str = ""
    NEMO_LLM_BASE_URL: str = "https://api.openai.com/v1"
    NEMO_LLM_API_KEY: str = "sk-proj-your-key-here"
    NEMO_LLM_MODEL: str = "gpt-4o-mini"

    # Qdrant
    QDRANT_URL: str = "http://localhost:6333"
    QDRANT_API_KEY: str = ""
    PRODUCTS_COLLECTION: str = "healthpilot_products"

    # Vector sync job
    VECTOR_SYNC_INTERVAL_SECONDS: int = 30
    VECTOR_SYNC_MAX_ATTEMPTS: int = 10

    # Logging
    LOG_LEVEL: str = "INFO"

    @model_validator(mode="after")
    def _normalize_database_url(self) -> "Settings":
        self.DATABASE_URL = normalize_database_url(self.DATABASE_URL)
        return self


@lru_cache()
def get_settings() -> Settings:
    """Returns a cached Settings instance."""
    return Settings()
