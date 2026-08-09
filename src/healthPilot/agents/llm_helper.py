"""Run user-facing text through the privacy pipeline."""

from __future__ import annotations

from healthPilot.agents.graph import coach_graph


async def run_user_facing_llm(prompt: str) -> str:
    result = await coach_graph.ainvoke(
        {
            "raw_text": prompt,
            "user_facing": True,
            "messages": [],
            "biomarkers": {},
        }
    )
    if result.get("error"):
        return "We have a wellness suggestion for you based on your recent browsing."
    return result.get("final_response") or result.get("llm_response") or ""
