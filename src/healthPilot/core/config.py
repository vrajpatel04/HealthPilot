from functools import lru_cache
from typing import List, Union
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Project settings
    PROJECT_NAME: str = "HealthPilot"
    PROJECT_DESCRIPTION: str = "An Agentic AI Lifestyle Recommendation System Backend API"
    VERSION: str = "0.0.0"
    API_V1_STR: str = "/api/v1"
    # ALLOWED_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:8000"]
    ALLOWED_ORIGINS: List[str] = ["*"]

    # API Settings
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000

    # OpenAI Configuration (Required)
    OPENAI_BASE_URL: str = "https://api.openai.com/v1"
    OPENAI_API_KEY: str = "sk-proj-your-key-here"

    # Logging
    LOG_LEVEL: str = "INFO"

    class Config:
        case_sensitive = True
        env_file = ".env"
        env_file_encoding = "utf-8"

        # Allow extra fields from .env file
        # extra = "allow"
        extra = "ignore"


@lru_cache()
def get_settings() -> Settings:
    """
    Returns a cached Settings instance.
    Use this everywhere instead of instantiating Settings() directly.

    Usage:
        from healthPilot.core.config import get_settings
        settings = get_settings()
    """
    return Settings()
