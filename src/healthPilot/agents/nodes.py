"""LangGraph nodes for the privacy pipeline (Presidio → NeMo → LLM)."""

from __future__ import annotations

from typing import Any

from langchain_core.messages import AIMessage, HumanMessage
from langchain_openai import ChatOpenAI

from healthPilot.agents.state import CoachState
from healthPilot.core.config import get_settings
from healthPilot.privacy.exceptions import (
    GuardrailsUnavailableError,
    PresidioUnavailableError,
    PrivacyPipelineBlockedError,
)
from healthPilot.privacy.guardrails_client import GuardrailsClient
from healthPilot.privacy.presidio_client import PresidioClient
from healthPilot.privacy.token_vault import TokenVault


def _latest_user_text(state: CoachState) -> str:
    if state.get("raw_text"):
        return state["raw_text"]
    for message in reversed(state.get("messages", [])):
        if isinstance(message, HumanMessage):
            return str(message.content)
    return ""


async def presidio_deidentify_node(state: CoachState) -> dict[str, Any]:
    text = _latest_user_text(state)
    if not text.strip():
        return {"error": "No user text to process"}

    presidio = PresidioClient()
    try:
        deidentified, vault = await presidio.deidentify(text)
    except PresidioUnavailableError as exc:
        return {"error": f"Presidio unavailable: {exc}"}

    return {
        "deidentified_text": deidentified,
        "raw_text": text,
        "token_vault": vault.as_dict(),
        "error": "",
    }


async def guardrail_input_node(state: CoachState) -> dict[str, Any]:
    text = state.get("deidentified_text") or ""
    if not text.strip():
        return {"error": state.get("error") or "Missing de-identified text"}

    guardrails = GuardrailsClient()
    try:
        validated = await guardrails.check_input(text)
    except PrivacyPipelineBlockedError as exc:
        return {"error": f"Input blocked: {exc.reason}"}
    except GuardrailsUnavailableError as exc:
        return {"error": f"Guardrails unavailable: {exc}"}

    return {"deidentified_text": validated, "error": ""}


async def llm_call_node(state: CoachState) -> dict[str, Any]:
    if state.get("error"):
        return {}

    settings = get_settings()
    text = state.get("deidentified_text") or ""
    biomarkers = state.get("biomarkers") or {}

    biomarker_lines = "\n".join(f"- {key}: {value}" for key, value in biomarkers.items())
    system_prompt = (
        "You are HealthPilot, a wellness coach. Provide lifestyle guidance only. "
        "Do not diagnose or prescribe. Keep responses concise."
    )
    user_content = text
    if biomarker_lines:
        user_content = f"{text}\n\nStructured biomarkers:\n{biomarker_lines}"

    llm = ChatOpenAI(
        base_url=settings.OPENAI_BASE_URL,
        api_key=settings.OPENAI_API_KEY,
        model=settings.LLM_MODEL,
        temperature=settings.LLM_TEMPERATURE,
    )

    try:
        response = await llm.ainvoke(
            [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content},
            ]
        )
    except Exception as exc:
        return {"error": f"LLM call failed: {exc}"}

    llm_text = str(response.content)
    return {"llm_response": llm_text}


async def guardrail_output_node(state: CoachState) -> dict[str, Any]:
    if state.get("error"):
        return {}

    user_facing = state.get("user_facing", True)
    llm_response = state.get("llm_response") or ""
    user_text = state.get("deidentified_text") or ""

    if not user_facing:
        return {"validated_response": llm_response}

    guardrails = GuardrailsClient()
    try:
        validated = await guardrails.check_output(llm_response, user_text)
    except PrivacyPipelineBlockedError as exc:
        return {"error": f"Output blocked: {exc.reason}"}
    except GuardrailsUnavailableError as exc:
        return {"error": f"Guardrails unavailable: {exc}"}

    return {"validated_response": validated}


async def presidio_deanonymize_node(state: CoachState) -> dict[str, Any]:
    """Restore tokenized PII in the validated response before returning to the user."""
    if state.get("error"):
        return {}

    validated = state.get("validated_response") or state.get("llm_response") or ""
    vault_map = state.get("token_vault") or {}
    user_facing = state.get("user_facing", True)

    if not user_facing or not vault_map:
        final = validated
    else:
        presidio = PresidioClient()
        vault = TokenVault.from_dict(vault_map)
        final = presidio.deanonymize(validated, vault)

    return {
        "final_response": final,
        "messages": [AIMessage(content=final)],
    }


def route_on_error(state: CoachState) -> str:
    if state.get("error"):
        return "error"
    return "continue"
