from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

from healthPilot.privacy.pipeline import PipelineInput, PrivacyPipeline
from healthPilot.privacy.token_vault import TokenVault


@pytest.mark.asyncio
async def test_internal_pipeline_skips_input_guardrails():
  pipeline = PrivacyPipeline()
  deidentified = "x" * 20_000

  with (
    patch.object(
      pipeline._presidio,
      "deidentify",
      new=AsyncMock(return_value=(deidentified, TokenVault())),
    ),
    patch.object(
      pipeline._guardrails,
      "check_input",
      new=AsyncMock(),
    ) as check_input,
  ):
    result = await pipeline.run(
      PipelineInput(text="raw report", user_facing=False),
      llm_call=AsyncMock(return_value='{"biomarkers": []}'),
    )

  check_input.assert_not_called()
  assert result.deidentified_text == deidentified


@pytest.mark.asyncio
async def test_user_facing_pipeline_runs_input_guardrails():
  pipeline = PrivacyPipeline()
  deidentified = "deidentified text"
  validated = "validated text"

  with (
    patch.object(
      pipeline._presidio,
      "deidentify",
      new=AsyncMock(return_value=(deidentified, TokenVault())),
    ),
    patch.object(
      pipeline._guardrails,
      "check_input",
      new=AsyncMock(return_value=validated),
    ) as check_input,
    patch.object(
      pipeline._guardrails,
      "check_output",
      new=AsyncMock(return_value="llm response"),
    ),
  ):
    result = await pipeline.run(
      PipelineInput(text="hello", user_facing=True),
      llm_call=AsyncMock(return_value="llm response"),
    )

  check_input.assert_awaited_once_with(deidentified)
  assert result.deidentified_text == validated
