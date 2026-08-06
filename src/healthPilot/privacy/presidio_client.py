"""Embedded Presidio PII detection and de-identification."""

from __future__ import annotations

import asyncio
from typing import Any

from presidio_anonymizer.entities import OperatorConfig

from healthPilot.core.config import Settings, get_settings
from healthPilot.privacy.exceptions import PresidioUnavailableError
from healthPilot.privacy.presidio_engine import analyze, anonymize, warmup_presidio
from healthPilot.privacy.token_vault import TokenVault


class PresidioClient:
    def __init__(self, settings: Settings | None = None):
        self._settings = settings or get_settings()

    async def health_ok(self) -> bool:
        try:
            await asyncio.to_thread(warmup_presidio)
            return True
        except Exception:
            return False

    async def analyze(self, text: str, language: str = "en") -> list[dict[str, Any]]:
        try:
            results = await asyncio.to_thread(
                analyze,
                text,
                language=language,
                score_threshold=self._settings.PRESIDIO_SCORE_THRESHOLD,
            )
            return [
                {
                    "start": item.start,
                    "end": item.end,
                    "score": item.score,
                    "entity_type": item.entity_type,
                }
                for item in results
            ]
        except Exception as exc:
            raise PresidioUnavailableError(str(exc)) from exc

    async def anonymize(
        self,
        text: str,
        analyzer_results: list,
        operators: dict[str, OperatorConfig],
    ) -> str:
        try:
            return await asyncio.to_thread(
                anonymize,
                text,
                analyzer_results,
                operators,
            )
        except Exception as exc:
            raise PresidioUnavailableError(str(exc)) from exc

    async def deidentify(self, text: str, vault: TokenVault | None = None) -> tuple[str, TokenVault]:
        """Analyze and tokenize direct identifiers."""
        vault = vault or TokenVault()

        try:
            results = await asyncio.to_thread(
                analyze,
                text,
                language="en",
                score_threshold=self._settings.PRESIDIO_SCORE_THRESHOLD,
            )
        except Exception as exc:
            raise PresidioUnavailableError(str(exc)) from exc

        if not results:
            return text, vault

        operators: dict[str, OperatorConfig] = {}
        for item in results:
            if item.entity_type not in operators:
                original = text[item.start : item.end]
                token = vault.tokenize(item.entity_type, original)
                operators[item.entity_type] = OperatorConfig(
                    "replace",
                    {"new_value": token},
                )

        deidentified = await self.anonymize(text, results, operators)
        return deidentified, vault

    def deanonymize(self, text: str, vault: TokenVault) -> str:
        """Restore original identifiers from token placeholders before returning to the user."""
        if not vault.as_dict():
            return text
        return vault.detokenize(text)

    def redact_for_logs(self, text: str) -> str:
        """Best-effort synchronous redaction label for log lines."""
        return "[REDACTED_TEXT]" if text.strip() else text
