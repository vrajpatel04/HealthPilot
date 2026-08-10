import hashlib
import json
from typing import Any

from healthPilot.services.behavior_hash import compute_behavior_hash


def compute_health_hash(
    *,
    events: list[dict[str, Any]],
    health_profile: dict[str, Any] | None,
    blood_report_id: str | None = None,
) -> str:
    behavior_part = compute_behavior_hash(events)
    health_payload: dict[str, Any] = {}
    if health_profile:
        for key in (
            "sleep_average",
            "water_average",
            "activity_average",
            "screen_time_average",
            "mood_average",
            "stress_average",
            "energy_average",
            "days_in_window",
        ):
            if health_profile.get(key) is not None:
                health_payload[key] = health_profile[key]
    if blood_report_id:
        health_payload["blood_report_id"] = blood_report_id

    combined = json.dumps(
        {"behavior": behavior_part, "health": health_payload},
        sort_keys=True,
        default=str,
    )
    return hashlib.sha256(combined.encode()).hexdigest()[:16]
