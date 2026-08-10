from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from healthPilot.api.deps import get_current_user
from healthPilot.core.database import get_db
from healthPilot.core.exceptions import AppError, NotFoundError
from healthPilot.models.health_profile import HealthProfile
from healthPilot.models.lifestyle_daily_log import LifestyleDailyLog
from healthPilot.models.user import User
from healthPilot.repositories.health_profile_repository import HealthProfileRepository
from healthPilot.repositories.lifestyle_repository import LifestyleRepository
from healthPilot.schemas.lifestyle import (
    DailyLogListResponse,
    DailyLogResponse,
    DailyLogUpsertRequest,
    DailyLogUpsertResponse,
    HealthProfileResponse,
    LifestyleResponses,
)
from healthPilot.services.lifestyle_service import LifestyleService

router = APIRouter()

_MAX_DATE_RANGE_DAYS = 90


def _log_to_response(log: LifestyleDailyLog) -> DailyLogResponse:
    return DailyLogResponse(
        id=log.id,
        log_date=log.log_date,
        responses=LifestyleResponses.model_validate(log.responses or {}),
        created_at=log.created_at,
        updated_at=log.updated_at,
    )


def _profile_to_response(profile: HealthProfile) -> HealthProfileResponse:
    metadata = profile.metadata_ or {}
    return HealthProfileResponse(
        sleep_average=profile.sleep_average,
        water_average=profile.water_average,
        activity_average=profile.activity_average,
        screen_time_average=profile.screen_time_average,
        mood_average=profile.mood_average,
        stress_average=profile.stress_average,
        energy_average=profile.energy_average,
        days_in_window=int(metadata.get("days_in_window", 0)),
    )


@router.get("/daily/today", response_model=DailyLogResponse)
async def get_today_log(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> DailyLogResponse:
    log = await LifestyleRepository(db).get_by_user_date(current_user.id, date.today())
    if log is None:
        raise NotFoundError("No log for today", code="LOG_NOT_FOUND")
    return _log_to_response(log)


@router.get("/daily", response_model=DailyLogListResponse)
async def list_daily_logs(
    from_date: Annotated[date, Query()],
    to_date: Annotated[date, Query()],
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> DailyLogListResponse:
    if from_date > to_date:
        raise AppError(
            "from_date must be on or before to_date",
            code="INVALID_DATE_RANGE",
            status_code=400,
        )
    if (to_date - from_date).days > _MAX_DATE_RANGE_DAYS:
        raise AppError(
            f"Date range cannot exceed {_MAX_DATE_RANGE_DAYS} days",
            code="DATE_RANGE_TOO_LARGE",
            status_code=400,
        )

    logs = await LifestyleRepository(db).list_in_range(
        current_user.id, from_date, to_date
    )
    return DailyLogListResponse(items=[_log_to_response(log) for log in logs])


@router.post("/daily", response_model=DailyLogUpsertResponse)
async def upsert_daily_log(
    body: DailyLogUpsertRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> DailyLogUpsertResponse:
    log, profile, material_change = await LifestyleService(db).upsert_daily_log(
        current_user.id,
        body.log_date,
        body.responses.model_dump(mode="json"),
    )
    return DailyLogUpsertResponse(
        log=_log_to_response(log),
        profile=_profile_to_response(profile),
        material_change=material_change,
    )


@router.get("/profile", response_model=HealthProfileResponse)
async def get_health_profile(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> HealthProfileResponse:
    profile = await HealthProfileRepository(db).get_by_user_id(current_user.id)
    if profile is None:
        raise NotFoundError("Health profile not found", code="PROFILE_NOT_FOUND")
    return _profile_to_response(profile)
