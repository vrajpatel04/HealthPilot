"""LangGraph state for the recommendation pipeline."""

from __future__ import annotations

import uuid
from typing import Any, TypedDict


class RecommendationState(TypedDict, total=False):
    user_id: uuid.UUID | None
    session_id: str
    events: list[dict[str, Any]]
    behavior_summary: dict[str, Any]
    user_memory: dict[str, Any]
    retrieval_query: str
    product_candidates: list[dict[str, Any]]
    rag_context: list[dict[str, Any]]
    evaluated_candidates: list[dict[str, Any]]
    primary_product_id: uuid.UUID | None
    secondary_product_id: uuid.UUID | None
    reason: str
    confidence: float
    persuasive_message: str
    why_recommended: list[str]
    behavior_hash: str
    errors: list[str]
    recommendation_id: uuid.UUID | None
