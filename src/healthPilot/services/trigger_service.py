from __future__ import annotations

from datetime import datetime, timedelta, timezone

from healthPilot.models.enums import EventType
from healthPilot.models.event import Event


class TriggerService:
    SEARCH_WINDOW_MINUTES = 30
    CATEGORY_WINDOW_MINUTES = 30

    def should_trigger(self, events: list[Event], *, manual: bool = False) -> bool:
        if manual:
            return True
        if not events:
            return False

        latest = events[-1]
        now = datetime.now(timezone.utc)
        recent_cutoff = now - timedelta(minutes=self.SEARCH_WINDOW_MINUTES)

        if latest.event_type == EventType.product_return:
            return True

        if latest.event_type == EventType.search:
            query = (latest.metadata_ or {}).get("query", "")
            prior_queries = {
                (e.metadata_ or {}).get("query")
                for e in events[:-1]
                if e.event_type == EventType.search and e.timestamp >= recent_cutoff
            }
            return query not in prior_queries

        if latest.event_type in (EventType.product_view, EventType.description_scroll):
            return self._category_interest_trigger(events)

        return False

    def _category_interest_trigger(self, events: list[Event]) -> bool:
        cutoff = datetime.now(timezone.utc) - timedelta(minutes=self.CATEGORY_WINDOW_MINUTES)
        recent = [e for e in events if e.timestamp >= cutoff]
        category_filters = [e for e in recent if e.event_type == EventType.category_filter]
        if not category_filters:
            return False
        category = (category_filters[-1].metadata_ or {}).get("category")
        if not category:
            return False
        views = [
            e
            for e in recent
            if e.event_type == EventType.product_view
            and (e.metadata_ or {}).get("category") == category
        ]
        return len(views) >= 2

    def should_trigger_after_lifestyle(
        self, *, material_change: bool, trend_alert: bool = False
    ) -> bool:
        return material_change or trend_alert
