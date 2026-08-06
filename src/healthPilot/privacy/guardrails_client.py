"""Embedded NeMo Guardrails validation."""

from __future__ import annotations

from enum import Enum
import logging

from nemoguardrails.rails.llm.options import RailStatus, RailType

from healthPilot.core.config import Settings, get_settings
from healthPilot.privacy.exceptions import GuardrailsUnavailableError, PrivacyPipelineBlockedError
from healthPilot.privacy.guardrails_engine import get_guardrails_engine, warmup_guardrails

logger = logging.getLogger(__name__)


class GuardrailCheckType(str, Enum):
    INPUT = "input"
    OUTPUT = "output"


class GuardrailsClient:
    def __init__(self, settings: Settings | None = None):
        self._settings = settings or get_settings()

    async def health_ok(self) -> bool:
        try:
            warmup_guardrails()
            return True
        except Exception as exc:
            logger.exception("NeMo Guardrails warmup failed: %s", exc)
            return False

    async def check_input(self, text: str) -> str:
        return await self._check(text, GuardrailCheckType.INPUT)

    async def check_output(self, assistant_text: str, user_text: str) -> str:
        return await self._check(
            assistant_text,
            GuardrailCheckType.OUTPUT,
            user_text=user_text,
        )

    async def _check(
        self,
        text: str,
        check_type: GuardrailCheckType,
        user_text: str | None = None,
    ) -> str:
        messages = self._messages_for_check(text, check_type, user_text)
        rail_type = (
            RailType.INPUT if check_type == GuardrailCheckType.INPUT else RailType.OUTPUT
        )

        try:
            rails = get_guardrails_engine()
            result = await rails.check_async(messages, rail_types=[rail_type])
        except Exception as exc:
            message = "NeMo Guardrails unavailable for user-facing output"
            if check_type == GuardrailCheckType.INPUT:
                message = str(exc)
            raise GuardrailsUnavailableError(message) from exc

        if result.status == RailStatus.BLOCKED:
            raise PrivacyPipelineBlockedError(
                stage=check_type.value,
                reason=result.content or "Content blocked by guardrails",
                blocked_by=result.rail,
            )

        return result.content or text

    @staticmethod
    def _messages_for_check(
        text: str,
        check_type: GuardrailCheckType,
        user_text: str | None,
    ) -> list[dict[str, str]]:
        if check_type == GuardrailCheckType.INPUT:
            return [{"role": "user", "content": text}]

        return [
            {"role": "user", "content": user_text or ""},
            {"role": "assistant", "content": text},
        ]
