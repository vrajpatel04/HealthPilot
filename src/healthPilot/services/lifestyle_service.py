from __future__ import annotations

import uuid
from datetime import date, timedelta
from decimal import Decimal
from typing import Any

from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession

from healthPilot.models.health_profile import HealthProfile
from healthPilot.models.lifestyle_daily_log import LifestyleDailyLog
from healthPilot.repositories.health_profile_repository import HealthProfileRepository
from healthPilot.repositories.lifestyle_repository import LifestyleRepository
from healthPilot.services.user_memory_vector_service import UserMemoryVectorService

LIFESTYLE_AGGREGATE_WINDOW_DAYS = 7
LIFESTYLE_TREND_SLEEP_DELTA_HOURS = 1.0

ACTIVITY_NUMERIC: dict[str, int] = {
    "sedentary": 1,
    "light": 2,
    "moderate": 3,
    "active": 4,
}

_NUMERIC_RESPONSE_FIELDS = (
    "sleep_hours",
    "water_glasses",
    "screen_hours",
    "mood",
    "stress",
    "energy",
)


def _activity_numeric(activity_level: str) -> int:
    return ACTIVITY_NUMERIC[activity_level]


def compute_aggregates_from_logs(logs: list[dict]) -> dict[str, Any]:
    if not logs:
        return {
            "sleep_average": None,
            "water_average": None,
            "activity_average": None,
            "screen_time_average": None,
            "mood_average": None,
            "stress_average": None,
            "energy_average": None,
            "days_in_window": 0,
        }

    sleep_values: list[float] = []
    water_values: list[int] = []
    activity_values: list[int] = []
    screen_values: list[float] = []
    mood_values: list[int] = []
    stress_values: list[int] = []
    energy_values: list[int] = []

    for log in logs:
        responses = log.get("responses") or {}
        sleep_values.append(float(responses["sleep_hours"]))
        water_values.append(int(responses["water_glasses"]))
        activity_values.append(_activity_numeric(responses["activity_level"]))
        screen_values.append(float(responses["screen_hours"]))
        mood_values.append(int(responses["mood"]))
        stress_values.append(int(responses["stress"]))
        energy_values.append(int(responses["energy"]))

    count = len(logs)

    def avg_float(values: list[float]) -> float:
        return sum(values) / count

    def avg_int(values: list[int]) -> float:
        return sum(values) / count

    return {
        "sleep_average": avg_float(sleep_values),
        "water_average": avg_float([float(v) for v in water_values]),
        "activity_average": avg_int(activity_values),
        "screen_time_average": avg_float(screen_values),
        "mood_average": avg_int(mood_values),
        "stress_average": avg_int(stress_values),
        "energy_average": avg_int(energy_values),
        "days_in_window": count,
    }


class LifestyleService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.lifestyle_repo = LifestyleRepository(session)
        self.profile_repo = HealthProfileRepository(session)

    @staticmethod
    def responses_materially_changed(old: dict, new: dict) -> bool:
        for field in _NUMERIC_RESPONSE_FIELDS:
            if abs(float(old.get(field, 0)) - float(new.get(field, 0))) >= 1:
                return True
        old_activity = _activity_numeric(old.get("activity_level", "sedentary"))
        new_activity = _activity_numeric(new.get("activity_level", "sedentary"))
        if abs(old_activity - new_activity) >= 1:
            return True
        return False

    @staticmethod
    def build_daily_snippet(responses: dict, log_date: date) -> str:
        activity = responses.get("activity_level", "unknown")
        return (
            f"Daily check-in {log_date.isoformat()}: "
            f"sleep {responses.get('sleep_hours')}h, "
            f"stress {responses.get('stress')}/5, "
            f"mood {responses.get('mood')}/5, "
            f"energy {responses.get('energy')}/5, "
            f"water {responses.get('water_glasses')} glasses, "
            f"screen {responses.get('screen_hours')}h, "
            f"activity {activity}"
        )

    @staticmethod
    def detect_sleep_trend(
        current_sleep_avg: float | None, prior_sleep_avg: float | None
    ) -> bool:
        if current_sleep_avg is None or prior_sleep_avg is None:
            return False
        return prior_sleep_avg - current_sleep_avg >= LIFESTYLE_TREND_SLEEP_DELTA_HOURS

    async def upsert_daily_log(
        self, user_id: uuid.UUID, log_date: date, responses: dict
    ) -> tuple[LifestyleDailyLog, HealthProfile, bool]:
        if log_date > date.today():
            raise ValidationError.from_exception_data(
                "DailyLogUpsertRequest",
                [
                    {
                        "type": "value_error",
                        "loc": ("log_date",),
                        "msg": "log_date cannot be in the future",
                        "input": log_date,
                    }
                ],
            )

        existing = await self.lifestyle_repo.get_by_user_date(user_id, log_date)
        material_change = existing is None or self.responses_materially_changed(
            existing.responses or {}, responses
        )

        log = await self.lifestyle_repo.upsert(
            LifestyleDailyLog(
                user_id=user_id,
                log_date=log_date,
                responses=responses,
            )
        )

        from_date = log_date - timedelta(days=LIFESTYLE_AGGREGATE_WINDOW_DAYS - 1)
        logs = await self.lifestyle_repo.list_in_range(user_id, from_date, log_date)
        agg = compute_aggregates_from_logs(
            [{"responses": entry.responses} for entry in logs]
        )

        profile = await self.profile_repo.upsert(
            HealthProfile(
                user_id=user_id,
                sleep_average=_to_decimal(agg["sleep_average"], 1),
                water_average=_to_decimal(agg["water_average"], 1),
                activity_average=_to_decimal(agg["activity_average"], 2),
                screen_time_average=_to_decimal(agg["screen_time_average"], 1),
                mood_average=_to_decimal(agg["mood_average"], 2),
                stress_average=_to_decimal(agg["stress_average"], 2),
                energy_average=_to_decimal(agg["energy_average"], 2),
                metadata_={"days_in_window": agg["days_in_window"]},
            )
        )

        await self.session.commit()

        vector_svc = UserMemoryVectorService()
        await vector_svc.write_snippet(
            user_id=user_id,
            memory_type="lifestyle_daily",
            source_id=f"{user_id}:{log_date.isoformat()}",
            text=self.build_daily_snippet(responses, log_date),
        )

        return log, profile, material_change


def _to_decimal(value: float | None, places: int) -> Decimal | None:
    if value is None:
        return None
    quantize = Decimal("0.1") if places == 1 else Decimal("0.01")
    return Decimal(str(value)).quantize(quantize)
