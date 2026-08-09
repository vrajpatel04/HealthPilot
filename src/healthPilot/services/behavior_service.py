from __future__ import annotations

from typing import Any

from healthPilot.models.enums import EventType
from healthPilot.models.event import Event


class BehaviorService:
    CATEGORY_KEYWORDS = {
        "sleep": "sleep improvement",
        "fitness": "fitness",
        "nutrition": "nutrition",
        "mental_wellness": "stress management",
        "lifestyle": "lifestyle",
    }

    def summarize(self, events: list[Event]) -> dict[str, Any]:
        if not events:
            return {
                "primary_interest": "general wellness",
                "secondary_interest": None,
                "engagement": "low",
                "high_intent_product_id": None,
                "search_topics": [],
            }

        category_counts: dict[str, int] = {}
        product_views: dict[str, int] = {}
        search_topics: list[str] = []

        for event in events:
            if event.event_type == EventType.search:
                query = (event.metadata_ or {}).get("query")
                if query and query not in search_topics:
                    search_topics.append(str(query))
            if event.event_type == EventType.category_filter:
                cat = (event.metadata_ or {}).get("category")
                if cat:
                    category_counts[str(cat)] = category_counts.get(str(cat), 0) + 2
            if event.event_type in (EventType.product_view, EventType.product_return):
                if event.product_id:
                    pid = str(event.product_id)
                    product_views[pid] = product_views.get(pid, 0) + 1
                    cat = (event.metadata_ or {}).get("category")
                    if cat:
                        category_counts[str(cat)] = category_counts.get(str(cat), 0) + 1

        primary_category = max(category_counts, key=category_counts.get) if category_counts else None
        primary_interest = self.CATEGORY_KEYWORDS.get(primary_category or "", "general wellness")
        if search_topics:
            primary_interest = search_topics[0]

        secondary = None
        if len(search_topics) > 1:
            secondary = search_topics[1]
        elif len(category_counts) > 1:
            sorted_cats = sorted(category_counts.items(), key=lambda x: x[1], reverse=True)
            secondary = self.CATEGORY_KEYWORDS.get(sorted_cats[1][0], sorted_cats[1][0])

        high_intent = max(product_views, key=product_views.get) if product_views else None
        total_signals = len(events) + sum(product_views.values())
        engagement = "high" if total_signals >= 8 else "medium" if total_signals >= 3 else "low"

        return {
            "primary_interest": primary_interest,
            "secondary_interest": secondary,
            "engagement": engagement,
            "high_intent_product_id": high_intent,
            "search_topics": search_topics,
            "primary_category": primary_category,
        }

    def build_why_recommended(self, events: list[Event], behavior: dict[str, Any]) -> list[str]:
        reasons: list[str] = []
        for topic in behavior.get("search_topics", [])[:2]:
            reasons.append(f'You searched for "{topic}"')
        returns = sum(1 for e in events if e.event_type == EventType.product_return)
        if returns:
            reasons.append("You returned to a product after exploring other options")
        views = sum(1 for e in events if e.event_type == EventType.product_view)
        if views >= 2:
            reasons.append(f"You viewed {views} products in this browsing session")
        scrolls = [e for e in events if e.event_type == EventType.description_scroll]
        if scrolls:
            pct = max((e.metadata_ or {}).get("scroll_percent", 0) for e in scrolls)
            if pct >= 50:
                reasons.append("You read a substantial portion of product descriptions")
        if not reasons:
            reasons.append("Based on your recent wellness browsing activity")
        return reasons
