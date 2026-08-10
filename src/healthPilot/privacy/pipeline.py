"""Privacy pipeline: Presidio → NeMo Guardrails → LLM."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from healthPilot.privacy.exceptions import PresidioUnavailableError
from healthPilot.privacy.guardrails_client import GuardrailsClient
from healthPilot.privacy.presidio_client import PresidioClient
from healthPilot.privacy.token_vault import TokenVault


@dataclass
class PipelineInput:
    text: str
    biomarkers: dict[str, Any] = field(default_factory=dict)
    user_facing: bool = True


@dataclass
class PipelineResult:
    original_text: str
    deidentified_text: str
    llm_response: str
    validated_response: str
    final_response: str
    token_vault: TokenVault
    biomarkers: dict[str, Any]


class PrivacyPipeline:
    """Orchestrates Presidio de-identification before NeMo and external LLM calls."""

    def __init__(
        self,
        presidio: PresidioClient | None = None,
        guardrails: GuardrailsClient | None = None,
    ):
        self._presidio = presidio or PresidioClient()
        self._guardrails = guardrails or GuardrailsClient()

    async def prepare_for_llm(
        self,
        text: str,
        vault: TokenVault | None = None,
        *,
        user_facing: bool = True,
    ) -> tuple[str, TokenVault]:
        """Presidio → NeMo input rail (user-facing only). Must run before any external LLM call."""
        try:
            deidentified, vault = await self._presidio.deidentify(text, vault)
        except PresidioUnavailableError:
            raise

        if not user_facing:
            return deidentified, vault

        validated = await self._guardrails.check_input(deidentified)
        return validated, vault

    async def validate_output(
        self,
        assistant_text: str,
        user_text: str,
        *,
        user_facing: bool = True,
    ) -> str:
        if not user_facing:
            return assistant_text
        return await self._guardrails.check_output(assistant_text, user_text)

    async def run(
        self,
        pipeline_input: PipelineInput,
        llm_call,
    ) -> PipelineResult:
        """
        Full pipeline: Presidio → NeMo input → LLM callable → NeMo output (if user-facing).
        `llm_call` receives (deidentified_text, biomarkers) and returns response text.
        """
        validated_input, vault = await self.prepare_for_llm(
            pipeline_input.text,
            user_facing=pipeline_input.user_facing,
        )
        llm_response = await llm_call(validated_input, pipeline_input.biomarkers)
        validated_response = await self.validate_output(
            llm_response,
            validated_input,
            user_facing=pipeline_input.user_facing,
        )
        if pipeline_input.user_facing and vault.as_dict():
            final_response = self._presidio.deanonymize(validated_response, vault)
        else:
            final_response = validated_response

        return PipelineResult(
            original_text=pipeline_input.text,
            deidentified_text=validated_input,
            llm_response=llm_response,
            validated_response=validated_response,
            final_response=final_response,
            token_vault=vault,
            biomarkers=pipeline_input.biomarkers,
        )
