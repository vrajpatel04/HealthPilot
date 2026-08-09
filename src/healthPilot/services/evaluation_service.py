from __future__ import annotations

from typing import Any


class EvaluationService:
    def score_candidates(
        self,
        candidates: list[dict[str, Any]],
        behavior: dict[str, Any],
        user_memory: dict[str, Any],
    ) -> list[dict[str, Any]]:
        primary_category = behavior.get("primary_category")
        high_intent = behavior.get("high_intent_product_id")
        successful = {
            str(item.get("product_id"))
            for item in user_memory.get("successful_recommendations", [])
        }

        scored: list[dict[str, Any]] = []
        for candidate in candidates:
            semantic = float(candidate.get("score", 0.5))
            category = candidate.get("category")
            behavior_match = 1.0 if primary_category and category == primary_category else 0.4
            memory_boost = 0.8 if str(candidate.get("product_id")) in successful else 0.0
            engagement = 1.0 if high_intent and str(candidate.get("product_id")) == high_intent else 0.3
            price = float(candidate.get("price", 0))
            price_fit = 0.7 if price <= 500 else 0.5

            final = (
                0.40 * semantic
                + 0.25 * behavior_match
                + 0.15 * memory_boost
                + 0.10 * price_fit
                + 0.10 * engagement
            )
            scored.append({**candidate, "final_score": round(final, 4)})

        return sorted(scored, key=lambda x: x["final_score"], reverse=True)
