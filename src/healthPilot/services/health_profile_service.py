from __future__ import annotations

import uuid
from datetime import date
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from healthPilot.repositories.health_profile_repository import HealthProfileRepository
from healthPilot.repositories.lifestyle_repository import LifestyleRepository


class HealthProfileService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.profile_repo = HealthProfileRepository(session)
        self.lifestyle_repo = LifestyleRepository(session)

    async def get_snapshot(self, user_id: uuid.UUID) -> dict[str, Any]:
        today = date.today()
        today_log = await self.lifestyle_repo.get_by_user_date(user_id, today)
        profile = await self.profile_repo.get_by_user_id(user_id)

        snapshot: dict[str, Any] = {
            "today_log": today_log.responses if today_log else None,
            "log_date": today.isoformat(),
        }
        if profile:
            metadata = profile.metadata_ or {}
            snapshot.update(
                {
                    "sleep_average": float(profile.sleep_average)
                    if profile.sleep_average is not None
                    else None,
                    "water_average": float(profile.water_average)
                    if profile.water_average is not None
                    else None,
                    "activity_average": float(profile.activity_average)
                    if profile.activity_average is not None
                    else None,
                    "screen_time_average": float(profile.screen_time_average)
                    if profile.screen_time_average is not None
                    else None,
                    "mood_average": float(profile.mood_average)
                    if profile.mood_average is not None
                    else None,
                    "stress_average": float(profile.stress_average)
                    if profile.stress_average is not None
                    else None,
                    "energy_average": float(profile.energy_average)
                    if profile.energy_average is not None
                    else None,
                    "days_in_window": int(metadata.get("days_in_window", 0)),
                }
            )
        return snapshot

    @staticmethod
    def profile_dict_from_snapshot(snapshot: dict[str, Any]) -> dict[str, Any] | None:
        if snapshot.get("days_in_window", 0) == 0 and snapshot.get("today_log") is None:
            return None
        return {
            key: snapshot.get(key)
            for key in (
                "sleep_average",
                "water_average",
                "activity_average",
                "screen_time_average",
                "mood_average",
                "stress_average",
                "energy_average",
                "days_in_window",
            )
            if snapshot.get(key) is not None
        }
