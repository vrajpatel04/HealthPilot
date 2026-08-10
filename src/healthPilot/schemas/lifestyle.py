from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from healthPilot.models.enums import ActivityLevel


class LifestyleResponses(BaseModel):
    sleep_hours: float = Field(ge=0, le=24)
    water_glasses: int = Field(ge=0, le=20)
    activity_level: ActivityLevel
    screen_hours: float = Field(ge=0, le=24)
    mood: int = Field(ge=1, le=5)
    stress: int = Field(ge=1, le=5)
    energy: int = Field(ge=1, le=5)
    notes: str | None = Field(default=None, max_length=500)


class DailyLogUpsertRequest(BaseModel):
    log_date: date
    responses: LifestyleResponses


class HealthProfileResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    sleep_average: Decimal | None = None
    water_average: Decimal | None = None
    activity_average: Decimal | None = None
    screen_time_average: Decimal | None = None
    mood_average: Decimal | None = None
    stress_average: Decimal | None = None
    energy_average: Decimal | None = None
    days_in_window: int = 0


class DailyLogResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    log_date: date
    responses: LifestyleResponses
    created_at: datetime
    updated_at: datetime


class DailyLogListResponse(BaseModel):
    items: list[DailyLogResponse]


class DailyLogUpsertResponse(BaseModel):
    log: DailyLogResponse
    profile: HealthProfileResponse
    material_change: bool
