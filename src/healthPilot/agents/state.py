"""LangGraph agent state for the privacy-aware coaching pipeline."""

from __future__ import annotations

from typing import Annotated, Any, TypedDict

from langgraph.graph.message import add_messages


class CoachState(TypedDict, total=False):
    messages: Annotated[list, add_messages]
    raw_text: str
    deidentified_text: str
    token_vault: dict[str, str]
    biomarkers: dict[str, Any]
    user_facing: bool
    llm_response: str
    validated_response: str
    final_response: str
    error: str
