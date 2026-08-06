from functools import lru_cache
from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict


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
    VERSION: str = "0.0.0"
    API_V1_STR: str = "/api/v1"
    ALLOWED_ORIGINS: List[str] = ["*"]

    # API Settings
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000

    # Agent LLM (Mesh API / OpenAI-compatible)
    OPENAI_BASE_URL: str = "https://api.openai.com/v1"
    OPENAI_API_KEY: str = "sk-proj-your-key-here"
    LLM_MODEL: str = "gpt-4o"
    LLM_MODEL_PROVIDER: str = "openai"
    LLM_TEMPERATURE: float = 0.0

    # Presidio (embedded)
    PRESIDIO_SCORE_THRESHOLD: float = 0.35
    PRESIDIO_SPACY_MODEL: str = "en_core_web_lg"

    # NeMo Guardrails (embedded)
    NEMO_CONFIG_PATH: str = ""
    NEMO_LLM_BASE_URL: str = "https://api.openai.com/v1"
    NEMO_LLM_API_KEY: str = "sk-proj-your-key-here"
    NEMO_LLM_MODEL: str = "gpt-4o-mini"

    # Logging
    LOG_LEVEL: str = "INFO"


@lru_cache()
def get_settings() -> Settings:
    """
    Returns a cached Settings instance.
    Use this everywhere instead of instantiating Settings() directly.
    """
    return Settings()
