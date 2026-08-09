from datetime import datetime, timedelta, timezone

from healthPilot.models.enums import EventType
from healthPilot.models.event import Event
from healthPilot.services.behavior_hash import compute_behavior_hash
from healthPilot.services.behavior_service import BehaviorService
from healthPilot.services.evaluation_service import EvaluationService
from healthPilot.services.trigger_service import TriggerService


def _event(event_type: EventType, **metadata) -> Event:
    return Event(
        session_id="sess-1",
        event_type=event_type,
        metadata_=metadata,
        timestamp=datetime.now(timezone.utc),
    )


def test_compute_behavior_hash_stable():
    events = [{"event_type": "search", "metadata": {"query": "sleep"}}]
    assert compute_behavior_hash(events) == compute_behavior_hash(events)


def test_compute_behavior_hash_changes_with_events():
    a = [{"event_type": "search", "metadata": {"query": "sleep"}}]
    b = [{"event_type": "search", "metadata": {"query": "fitness"}}]
    assert compute_behavior_hash(a) != compute_behavior_hash(b)


def test_behavior_service_search_primary_interest():
    events = [_event(EventType.search, query="sleep improvement")]
    summary = BehaviorService().summarize(events)
    assert summary["primary_interest"] == "sleep improvement"


def test_evaluation_service_ranks_category_match_higher():
    evaluator = EvaluationService()
    behavior = {"primary_category": "sleep", "high_intent_product_id": None}
    memory = {"successful_recommendations": []}
    candidates = [
        {"product_id": "1", "category": "fitness", "score": 0.6, "price": 100},
        {"product_id": "2", "category": "sleep", "score": 0.5, "price": 100},
    ]
    ranked = evaluator.score_candidates(candidates, behavior, memory)
    assert ranked[0]["product_id"] == "2"


def test_trigger_on_product_return():
    events = [
        _event(EventType.product_view, category="sleep"),
        _event(EventType.product_return),
    ]
    assert TriggerService().should_trigger(events) is True


def test_trigger_on_new_search():
    events = [_event(EventType.search, query="nutrition")]
    assert TriggerService().should_trigger(events) is True


def test_trigger_skips_repeat_search():
    now = datetime.now(timezone.utc)
    events = [
        Event(
            session_id="s",
            event_type=EventType.search,
            metadata_={"query": "sleep"},
            timestamp=now - timedelta(minutes=5),
        ),
        Event(
            session_id="s",
            event_type=EventType.search,
            metadata_={"query": "sleep"},
            timestamp=now,
        ),
    ]
    assert TriggerService().should_trigger(events) is False


def test_null_cache_parity():
    import asyncio

    from healthPilot.cache.redis_cache import NullCache

    async def _run():
        cache = NullCache()
        await cache.set("k", "v")
        assert await cache.get("k") is None
        await cache.delete("k")
        await cache.delete_pattern("*")

    asyncio.run(_run())


def test_memory_service_handles_null_preferences():
    import asyncio
    from unittest.mock import AsyncMock, MagicMock

    from healthPilot.services.memory_service import MemoryService

    async def _run():
        session = AsyncMock()
        memory = MagicMock()
        memory.preferences = None
        memory.successful_recommendations = None
        memory.primary_interest = "sleep"
        memory.secondary_interest = None

        svc = MemoryService(session)
        svc.repo.get_for_actor = AsyncMock(return_value=memory)
        svc.repo.upsert = AsyncMock(return_value=memory)

        result = await svc.update_from_behavior(
            session_id="sess-1",
            user_id=None,
            behavior={"primary_interest": "sleep", "engagement": "medium"},
        )
        assert result["preferences"] == {
            "engagement": "medium",
            "content_type": "structured_programs",
        }
        assert memory.preferences == {
            "engagement": "medium",
            "content_type": "structured_programs",
        }

    asyncio.run(_run())
