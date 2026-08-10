"""Run text through the privacy pipeline for user-facing and internal LLM calls."""

from __future__ import annotations

from langchain_openai import ChatOpenAI

from healthPilot.agents.graph import coach_graph
from healthPilot.core.config import get_settings
from healthPilot.privacy.pipeline import PipelineInput, PrivacyPipeline


async def run_user_facing_llm(prompt: str) -> str:
    result = await coach_graph.ainvoke(
        {
            "raw_text": prompt,
            "user_facing": True,
            "messages": [],
            "biomarkers": {},
        }
    )
    if result.get("error"):
        return "We have a wellness suggestion for you based on your recent browsing."
    return result.get("final_response") or result.get("llm_response") or ""


async def run_internal_llm(prompt: str, *, system_prompt: str | None = None) -> str:
    """Presidio de-identify → guardrails input → LLM (no deanonymize on output)."""
    settings = get_settings()
    system = system_prompt or (
        "You extract structured wellness data from de-identified lab reports. "
        "Follow instructions exactly and return only the requested format."
    )

    async def llm_call(deidentified_text: str, _biomarkers: dict) -> str:
        llm = ChatOpenAI(
            base_url=settings.OPENAI_BASE_URL,
            api_key=settings.OPENAI_API_KEY,
            model=settings.LLM_MODEL,
            temperature=settings.LLM_TEMPERATURE,
        )
        response = await llm.ainvoke(
            [
                {"role": "system", "content": system},
                {"role": "user", "content": deidentified_text},
            ]
        )
        return str(response.content)

    result = await PrivacyPipeline().run(
        PipelineInput(text=prompt, user_facing=False),
        llm_call,
    )
    return result.validated_response or result.llm_response
