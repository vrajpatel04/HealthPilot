"""LangGraph nodes for the recommendation pipeline."""

from __future__ import annotations

import uuid
from typing import Any

from langchain_core.runnables.config import RunnableConfig

from healthPilot.agents.llm_helper import run_user_facing_llm
from healthPilot.agents.recommendation_state import RecommendationState
from healthPilot.services.behavior_service import BehaviorService
from healthPilot.services.blood_report_service import BloodReportService
from healthPilot.services.evaluation_service import EvaluationService
from healthPilot.services.health_profile_service import HealthProfileService
from healthPilot.services.memory_service import MemoryService
from healthPilot.services.retrieval_service import RetrievalService
from healthPilot.services.user_memory_vector_service import UserMemoryVectorService


def _session(config: RunnableConfig) -> Any:
    configurable = config.get("configurable") or {}
    return configurable["session"]


async def load_context_node(
    state: RecommendationState, config: RunnableConfig
) -> dict[str, Any]:
    session = _session(config)
    configurable = config.get("configurable") or {}
    event_repo = configurable["event_repository"]
    user_id = state.get("user_id")
    session_id = state["session_id"]
    settings = configurable["settings"]

    events = await event_repo.list_recent(
        session_id=session_id,
        user_id=user_id,
        hours=settings.BEHAVIOR_WINDOW_HOURS,
    )
    serialized = [
        {
            "event_type": e.event_type.value,
            "product_id": str(e.product_id) if e.product_id else None,
            "metadata": e.metadata_ or {},
            "timestamp": e.timestamp.isoformat(),
        }
        for e in events
    ]

    lifestyle_snapshot: dict[str, Any] = {}
    blood_report_summary = None
    if user_id:
        lifestyle_snapshot = await HealthProfileService(session).get_snapshot(user_id)
        blood_report_summary = await BloodReportService(session).get_summary_for_pipeline(user_id)

    return {
        "events": serialized,
        "lifestyle_snapshot": lifestyle_snapshot,
        "blood_report_summary": blood_report_summary,
    }


async def behavior_agent_node(
    state: RecommendationState, config: RunnableConfig
) -> dict[str, Any]:
    session = _session(config)
    configurable = config.get("configurable") or {}
    event_repo = configurable["event_repository"]
    behavior_svc = BehaviorService()

    user_id = state.get("user_id")
    session_id = state["session_id"]
    settings = configurable["settings"]
    events = await event_repo.list_recent(
        session_id=session_id,
        user_id=user_id,
        hours=settings.BEHAVIOR_WINDOW_HOURS,
    )

    summary = behavior_svc.summarize(events)
    why = behavior_svc.build_why_recommended(events, summary)
    lifestyle = state.get("lifestyle_snapshot") or {}
    if lifestyle.get("sleep_average") is not None and lifestyle["sleep_average"] < 6:
        summary["lifestyle_gaps"] = summary.get("lifestyle_gaps", []) + ["low_sleep"]
        why.append("Your recent sleep average is below 6 hours")
    if lifestyle.get("stress_average") is not None and lifestyle["stress_average"] >= 4:
        summary["lifestyle_gaps"] = summary.get("lifestyle_gaps", []) + ["high_stress"]
        why.append("You've reported elevated stress recently")

    query = summary.get("primary_interest") or "general wellness"
    if summary.get("secondary_interest"):
        query = f"{query} {summary['secondary_interest']}"
    if lifestyle.get("sleep_average") is not None and lifestyle["sleep_average"] < 6:
        query = f"{query} sleep improvement"
    if lifestyle.get("stress_average") is not None and lifestyle["stress_average"] >= 4:
        query = f"{query} stress management"

    return {
        "behavior_summary": summary,
        "retrieval_query": query,
        "why_recommended": why,
    }


async def memory_agent_node(
    state: RecommendationState, config: RunnableConfig
) -> dict[str, Any]:
    session = _session(config)
    memory_svc = MemoryService(session)
    user_id = state.get("user_id")
    session_id = state["session_id"]
    behavior = state.get("behavior_summary") or {}

    memory = await memory_svc.load(session_id=session_id, user_id=user_id)
    if behavior:
        memory = await memory_svc.update_from_behavior(
            session_id=session_id,
            user_id=user_id,
            behavior=behavior,
        )

    episodic: list[dict[str, Any]] = []
    if user_id:
        configurable = config.get("configurable") or {}
        settings = configurable["settings"]
        lifestyle = state.get("lifestyle_snapshot") or {}
        blood = state.get("blood_report_summary") or {}
        query_parts = [
            behavior.get("primary_interest") or "",
            str(lifestyle.get("sleep_average") or ""),
            str(lifestyle.get("stress_average") or ""),
            " ".join(blood.get("flags") or []),
        ]
        query = " ".join(part for part in query_parts if part).strip() or "wellness"
        episodic = await UserMemoryVectorService().search(
            user_id, query, limit=settings.USER_MEMORY_RETRIEVAL_K
        )
        memory["episodic_memories"] = episodic

    return {"user_memory": memory, "episodic_memories": episodic}


async def retrieval_agent_node(
    state: RecommendationState, config: RunnableConfig
) -> dict[str, Any]:
    session = _session(config)
    retrieval = RetrievalService(session)
    query = state.get("retrieval_query") or "wellness"
    behavior = state.get("behavior_summary") or {}
    category = behavior.get("primary_category")

    products = await retrieval.retrieve_products(query, limit=8, category=category)
    rag = await retrieval.retrieve_knowledge(query)
    return {"product_candidates": products, "rag_context": rag}


async def evaluation_agent_node(
    state: RecommendationState, config: RunnableConfig
) -> dict[str, Any]:
    evaluator = EvaluationService()
    candidates = state.get("product_candidates") or []
    behavior = state.get("behavior_summary") or {}
    memory = state.get("user_memory") or {}
    lifestyle = state.get("lifestyle_snapshot") or {}
    health_profile = HealthProfileService.profile_dict_from_snapshot(lifestyle)
    scored = evaluator.score_candidates(
        candidates,
        behavior,
        memory,
        health_profile=health_profile,
        blood_report_summary=state.get("blood_report_summary"),
    )
    return {"evaluated_candidates": scored}


async def recommendation_agent_node(
    state: RecommendationState, config: RunnableConfig
) -> dict[str, Any]:
    evaluated = state.get("evaluated_candidates") or []
    if not evaluated:
        return {
            "primary_product_id": None,
            "secondary_product_id": None,
            "reason": "No matching products found for your interests yet",
            "confidence": 0.0,
        }

    top = evaluated[0]
    second = evaluated[1] if len(evaluated) > 1 else None
    behavior = state.get("behavior_summary") or {}
    rag_snippets = " ".join(c.get("text", "")[:200] for c in (state.get("rag_context") or [])[:2])

    reason_prompt = (
        "Write one concise sentence explaining why this wellness product fits the user. "
        f"Product: {top.get('title')}. Interest: {behavior.get('primary_interest')}. "
        f"Context: {rag_snippets[:300]}"
    )
    reason = await run_user_facing_llm(reason_prompt)
    confidence = min(float(top.get("final_score", 0.5)), 0.99)

    return {
        "primary_product_id": uuid.UUID(str(top["product_id"])),
        "secondary_product_id": uuid.UUID(str(second["product_id"])) if second else None,
        "reason": reason.strip() or f"Strong match for {behavior.get('primary_interest', 'your interests')}",
        "confidence": round(confidence, 2),
    }


async def persuasion_agent_node(
    state: RecommendationState, config: RunnableConfig
) -> dict[str, Any]:
    session = _session(config)
    from healthPilot.repositories.product_repository import ProductRepository

    primary_id = state.get("primary_product_id")
    if not primary_id:
        tip = ""
        for chunk in state.get("rag_context") or []:
            if chunk.get("text"):
                tip = chunk["text"][:200]
                break
        message = tip or "Explore our marketplace to discover wellness programs tailored to you."
        return {"persuasive_message": message}

    product = await ProductRepository(session).get_by_id(primary_id)
    behavior = state.get("behavior_summary") or {}
    prompt = (
        "Write a friendly 2-sentence wellness recommendation message for the user. "
        "Do not diagnose. Encourage exploration.\n"
        f"Product: {product.title if product else 'wellness program'}\n"
        f"User interest: {behavior.get('primary_interest')}\n"
        f"Reason: {state.get('reason', '')}"
    )
    message = await run_user_facing_llm(prompt)
    if not message.strip():
        message = (
            f"You've been exploring {behavior.get('primary_interest', 'wellness')} — "
            f"we think {product.title if product else 'this program'} could be a great next step."
        )
    return {"persuasive_message": message.strip()}


async def store_recommendation_node(
    state: RecommendationState, config: RunnableConfig
) -> dict[str, Any]:
    session = _session(config)
    from datetime import datetime, timedelta, timezone
    from decimal import Decimal

    from healthPilot.models.recommendation import Recommendation
    from healthPilot.repositories.recommendation_repository import RecommendationRepository

    configurable = config.get("configurable") or {}
    settings = configurable["settings"]
    primary_id = state.get("primary_product_id")
    if not primary_id:
        return {"recommendation_id": None}

    product_ids = [str(primary_id)]
    secondary = state.get("secondary_product_id")
    if secondary:
        product_ids.append(str(secondary))

    now = datetime.now(timezone.utc)
    rec = Recommendation(
        user_id=state.get("user_id"),
        session_id=state["session_id"],
        primary_product_id=primary_id,
        secondary_product_id=secondary,
        product_ids=product_ids,
        message=state.get("persuasive_message") or "",
        reason=state.get("reason") or "",
        confidence=Decimal(str(state.get("confidence") or 0.5)),
        behavior_hash=state.get("behavior_hash") or "",
        behavior_summary=state.get("behavior_summary") or {},
        why_recommended=state.get("why_recommended") or [],
        expires_at=now + timedelta(hours=settings.RECOMMENDATION_TTL_HOURS),
    )
    stored = await RecommendationRepository(session).create(rec)
    await session.commit()
    return {"recommendation_id": stored.id}
