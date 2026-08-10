from __future__ import annotations

from typing import Any


class EvaluationService:
    def score_candidates(
        self,
        candidates: list[dict[str, Any]],
        behavior: dict[str, Any],
        user_memory: dict[str, Any],
        *,
        health_profile: dict[str, Any] | None = None,
        blood_report_summary: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        primary_category = behavior.get("primary_category")
        high_intent = behavior.get("high_intent_product_id")
        successful = {
            str(item.get("product_id"))
            for item in user_memory.get("successful_recommendations", [])
        }
        has_biomarkers = bool(blood_report_summary and blood_report_summary.get("flags"))

        scored: list[dict[str, Any]] = []
        for candidate in candidates:
            semantic = float(candidate.get("score", 0.5))
            category = candidate.get("category")
            behavior_match = 1.0 if primary_category and category == primary_category else 0.4
            memory_boost = 0.8 if str(candidate.get("product_id")) in successful else 0.0
            engagement = 1.0 if high_intent and str(candidate.get("product_id")) == high_intent else 0.3
            price = float(candidate.get("price", 0))
            price_fit = 0.7 if price <= 500 else 0.5
            lifestyle_fit = self._lifestyle_fit(category, health_profile)
            biomarker_relevance = (
                self._biomarker_relevance(candidate, blood_report_summary)
                if has_biomarkers
                else None
            )

            if has_biomarkers:
                final = (
                    0.30 * semantic
                    + 0.20 * behavior_match
                    + 0.12 * memory_boost
                    + 0.10 * price_fit
                    + 0.08 * engagement
                    + 0.10 * lifestyle_fit
                    + 0.10 * (biomarker_relevance or 0.0)
                )
            elif health_profile:
                final = (
                    0.33 * semantic
                    + 0.22 * behavior_match
                    + 0.13 * memory_boost
                    + 0.11 * price_fit
                    + 0.09 * engagement
                    + 0.12 * lifestyle_fit
                )
            else:
                final = (
                    0.40 * semantic
                    + 0.25 * behavior_match
                    + 0.15 * memory_boost
                    + 0.10 * price_fit
                    + 0.10 * engagement
                )

            row = {**candidate, "final_score": round(final, 4), "lifestyle_fit": lifestyle_fit}
            if biomarker_relevance is not None:
                row["biomarker_relevance"] = biomarker_relevance
            scored.append(row)

        return sorted(scored, key=lambda x: x["final_score"], reverse=True)

    @staticmethod
    def _lifestyle_fit(category: str | None, health_profile: dict[str, Any] | None) -> float:
        if not health_profile or not category:
            return 0.5
        sleep = health_profile.get("sleep_average")
        stress = health_profile.get("stress_average")
        activity = health_profile.get("activity_average")
        if sleep is not None and sleep < 6 and category == "sleep":
            return 1.0
        if stress is not None and stress >= 4 and category == "mental_wellness":
            return 1.0
        if activity is not None and activity < 2 and category == "fitness":
            return 1.0
        return 0.5

    @staticmethod
    def _biomarker_relevance(
        candidate: dict[str, Any], blood_report_summary: dict[str, Any] | None
    ) -> float:
        if not blood_report_summary:
            return 0.5
        flags = set(blood_report_summary.get("flags") or [])
        category = candidate.get("category")
        metadata = candidate.get("metadata") or {}
        text = f"{candidate.get('title', '')} {metadata}".lower()
        if "vitamin_d_low" in flags and category == "nutrition" and "vitamin" in text:
            return 1.0
        if "ldl_elevated" in flags and category in ("nutrition", "lifestyle"):
            return 0.8
        return 0.5
