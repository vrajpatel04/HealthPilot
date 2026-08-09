from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from healthPilot.agents.recommendation_graph import recommendation_graph
from healthPilot.cache.redis_cache import cache_get_json, cache_set_json, get_cache
from healthPilot.core.config import Settings, get_settings
from healthPilot.models.enums import FeedbackAction
from healthPilot.models.recommendation import Recommendation
from healthPilot.repositories.event_repository import EventRepository
from healthPilot.repositories.feedback_repository import FeedbackRepository
from healthPilot.repositories.product_repository import ProductRepository
from healthPilot.repositories.recommendation_repository import RecommendationRepository
from healthPilot.services.behavior_hash import actor_key, compute_behavior_hash
from healthPilot.services.trigger_service import TriggerService


class RecommendationOrchestrator:
    def __init__(self, session: AsyncSession, settings: Settings | None = None):
        self.session = session
        self.settings = settings or get_settings()
        self.events = EventRepository(session)
        self.recommendations = RecommendationRepository(session)
        self.products = ProductRepository(session)
        self.feedback = FeedbackRepository(session)
        self.triggers = TriggerService()

    def _cache_actor(self, *, session_id: str, user_id: uuid.UUID | None) -> str:
        return actor_key(user_id=str(user_id) if user_id else None, session_id=session_id)

    async def _current_behavior_hash(
        self, *, session_id: str, user_id: uuid.UUID | None
    ) -> tuple[str, list[dict[str, Any]]]:
        recent = await self.events.list_recent(
            session_id=session_id,
            user_id=user_id,
            hours=self.settings.BEHAVIOR_WINDOW_HOURS,
        )
        serialized = [
            {
                "event_type": e.event_type.value,
                "product_id": str(e.product_id) if e.product_id else None,
                "metadata": e.metadata_ or {},
                "timestamp": e.timestamp.isoformat(),
            }
            for e in recent
        ]
        return compute_behavior_hash(serialized), serialized

    async def _cooldown_active(self, actor: str) -> bool:
        key = f"trigger:cooldown:{actor}"
        cached = await (await get_cache()).get(key)
        return cached is not None

    async def _set_cooldown(self, actor: str) -> None:
        await (await get_cache()).set(
            key=f"trigger:cooldown:{actor}",
            value="1",
            ttl_seconds=self.settings.TRIGGER_COOLDOWN_SECONDS,
        )

    async def _serialize_rec(
        self, rec: Recommendation, *, cached: bool = False
    ) -> dict[str, Any]:
        primary = await self.products.get_by_id(rec.primary_product_id)
        secondary = None
        if rec.secondary_product_id:
            secondary = await self.products.get_by_id(rec.secondary_product_id)

        return {
            "id": str(rec.id),
            "primary_product": self._product_payload(primary) if primary else None,
            "secondary_product": self._product_payload(secondary) if secondary else None,
            "message": rec.message,
            "reason": rec.reason,
            "confidence": float(rec.confidence),
            "why_recommended": rec.why_recommended or [],
            "cached": cached,
            "created_at": rec.created_at.isoformat() if rec.created_at else None,
        }

    @staticmethod
    def _product_payload(product) -> dict[str, Any]:
        return {
            "id": str(product.id),
            "title": product.title,
            "description": product.description,
            "category": product.category.value,
            "price": str(product.price),
        }

    async def get_latest(
        self, *, session_id: str, user_id: uuid.UUID | None
    ) -> dict[str, Any] | None:
        actor = self._cache_actor(session_id=session_id, user_id=user_id)
        cached = await cache_get_json(f"rec:latest:{actor}")
        if cached:
            cached["cached"] = True
            return cached

        rec = await self.recommendations.get_latest(session_id=session_id, user_id=user_id)
        if not rec:
            return None
        if rec.expires_at and rec.expires_at.replace(tzinfo=timezone.utc) < datetime.now(timezone.utc):
            return None

        payload = await self._serialize_rec(rec, cached=False)
        ttl = self.settings.RECOMMENDATION_TTL_HOURS * 3600
        await cache_set_json(f"rec:latest:{actor}", payload, ttl)
        await cache_set_json(f"rec:behavior_hash:{actor}", rec.behavior_hash, ttl)
        return payload

    async def run_pipeline(
        self,
        *,
        session_id: str,
        user_id: uuid.UUID | None,
        manual: bool = False,
        bypass_cooldown: bool = False,
    ) -> dict[str, Any] | None:
        actor = self._cache_actor(session_id=session_id, user_id=user_id)
        behavior_hash, _ = await self._current_behavior_hash(
            session_id=session_id, user_id=user_id
        )

        if not manual:
            if await self._cooldown_active(actor):
                return await self.get_latest(session_id=session_id, user_id=user_id)
            cached_hash = await cache_get_json(f"rec:behavior_hash:{actor}")
            if cached_hash == behavior_hash:
                latest = await self.get_latest(session_id=session_id, user_id=user_id)
                if latest:
                    return latest

        recent_events = await self.events.list_recent(
            session_id=session_id,
            user_id=user_id,
            hours=self.settings.BEHAVIOR_WINDOW_HOURS,
        )
        if not recent_events and not manual:
            return None

        if not manual and not bypass_cooldown:
            if not self.triggers.should_trigger(recent_events, manual=False):
                return await self.get_latest(session_id=session_id, user_id=user_id)

        state = await recommendation_graph.ainvoke(
            {
                "user_id": user_id,
                "session_id": session_id,
                "behavior_hash": behavior_hash,
                "errors": [],
            },
            config={
                "configurable": {
                    "session": self.session,
                    "event_repository": self.events,
                    "settings": self.settings,
                }
            },
        )

        rec_id = state.get("recommendation_id")
        if not rec_id:
            return None

        await self._set_cooldown(actor)
        rec = await self.recommendations.get_by_id(rec_id)
        if not rec:
            return None

        payload = await self._serialize_rec(rec, cached=False)
        ttl = self.settings.RECOMMENDATION_TTL_HOURS * 3600
        await cache_set_json(f"rec:latest:{actor}", payload, ttl)
        await cache_set_json(f"rec:behavior_hash:{actor}", behavior_hash, ttl)
        return payload

    async def maybe_trigger_after_events(
        self, *, session_id: str, user_id: uuid.UUID | None
    ) -> None:
        await self.run_pipeline(session_id=session_id, user_id=user_id, manual=False)

    async def record_feedback(
        self,
        *,
        recommendation_id: uuid.UUID,
        action: FeedbackAction,
        user_id: uuid.UUID | None,
    ) -> None:
        rec = await self.recommendations.get_by_id(recommendation_id)
        if rec is None:
            from healthPilot.core.exceptions import NotFoundError

            raise NotFoundError("Recommendation not found", code="RECOMMENDATION_NOT_FOUND")
        await self.feedback.create(
            recommendation_id=recommendation_id,
            action=action,
            user_id=user_id,
        )
        await self.session.commit()

    async def has_browsing_activity(
        self, *, session_id: str, user_id: uuid.UUID | None
    ) -> bool:
        events = await self.events.list_recent(
            session_id=session_id,
            user_id=user_id,
            hours=self.settings.BEHAVIOR_WINDOW_HOURS,
            limit=1,
        )
        return len(events) > 0
