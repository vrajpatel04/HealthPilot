"""Embedded NeMo Guardrails engine."""

from __future__ import annotations

import logging
import os
from functools import lru_cache
from pathlib import Path

from nemoguardrails import LLMRails, RailsConfig

from healthPilot.core.config import Settings, get_settings

logger = logging.getLogger(__name__)

DEFAULT_CONFIG_DIR = Path(__file__).parent / "nemo_config"


def _resolve_config_path(settings: Settings) -> Path:
    configured_value = settings.NEMO_CONFIG_PATH.strip()
    if configured_value:
        configured = Path(configured_value)
        if configured.is_dir():
            return configured
        raise FileNotFoundError(f"NeMo config directory not found: {configured}")

    if DEFAULT_CONFIG_DIR.is_dir():
        return DEFAULT_CONFIG_DIR
    raise FileNotFoundError(f"NeMo config not found at {DEFAULT_CONFIG_DIR}")


def _apply_llm_env(settings: Settings) -> None:
    os.environ.setdefault("OPENAI_API_KEY", settings.NEMO_LLM_API_KEY)
    os.environ.setdefault("OPENAI_API_BASE", settings.NEMO_LLM_BASE_URL)


def _configure_models(config: RailsConfig, settings: Settings) -> None:
    if not config.models:
        return
    config.models[0].model = settings.NEMO_LLM_MODEL
    config.models[0].parameters = config.models[0].parameters or {}
    config.models[0].parameters["base_url"] = settings.NEMO_LLM_BASE_URL
    config.models[0].parameters["api_key"] = settings.NEMO_LLM_API_KEY
    config.models[0].parameters.pop("openai_api_base", None)


@lru_cache
def get_guardrails_engine() -> LLMRails:
    settings = get_settings()
    _apply_llm_env(settings)
    config_path = _resolve_config_path(settings)
    config = RailsConfig.from_path(str(config_path))
    _configure_models(config, settings)
    logger.info("NeMo Guardrails loaded from %s", config_path)
    return LLMRails(config)


def warmup_guardrails() -> None:
    get_guardrails_engine()
