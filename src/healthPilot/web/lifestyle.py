from datetime import date
from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Depends, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession

from healthPilot.core.config import get_settings
from healthPilot.core.database import get_db
from healthPilot.core.exceptions import AppError
from healthPilot.models.enums import ActivityLevel
from healthPilot.models.user import User
from healthPilot.repositories.health_profile_repository import HealthProfileRepository
from healthPilot.repositories.lifestyle_repository import LifestyleRepository
from healthPilot.services.lifestyle_service import LifestyleService
from healthPilot.web.deps import pop_flash, require_logged_in_user, set_flash, show_for_you_nav
from healthPilot.web.marketplace import _base_context
from healthPilot.web.templates_env import templates

router = APIRouter()


def _profile_dict(profile) -> dict | None:
    if profile is None:
        return None
    metadata = profile.metadata_ or {}
    return {
        "sleep_average": float(profile.sleep_average) if profile.sleep_average is not None else None,
        "water_average": float(profile.water_average) if profile.water_average is not None else None,
        "activity_average": float(profile.activity_average) if profile.activity_average is not None else None,
        "screen_time_average": float(profile.screen_time_average) if profile.screen_time_average is not None else None,
        "mood_average": float(profile.mood_average) if profile.mood_average is not None else None,
        "stress_average": float(profile.stress_average) if profile.stress_average is not None else None,
        "energy_average": float(profile.energy_average) if profile.energy_average is not None else None,
        "days_in_window": int(metadata.get("days_in_window", 0)),
    }


async def _trigger_recommendations_after_lifestyle(
    user_id, session_id: str | None, material_change: bool, trend_alert: bool
) -> None:
    if not session_id:
        return
    from healthPilot.core.database import AsyncSessionLocal
    from healthPilot.services.recommendation_orchestrator import RecommendationOrchestrator

    async with AsyncSessionLocal() as db:
        await RecommendationOrchestrator(db).maybe_trigger_after_lifestyle(
            session_id=session_id,
            user_id=user_id,
            material_change=material_change,
            trend_alert=trend_alert,
        )


@router.get("/lifestyle", response_class=HTMLResponse)
async def lifestyle_checkin_page(
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(require_logged_in_user)],
):
    show_for_you = await show_for_you_nav(request, db, user)
    today = date.today()
    today_log = await LifestyleRepository(db).get_by_user_date(user.id, today)
    profile = await HealthProfileRepository(db).get_by_user_id(user.id)
    responses = (today_log.responses if today_log else None) or {}

    return templates.TemplateResponse(
        request,
        "lifestyle/checkin.html",
        {
            **_base_context(request, user, show_for_you=show_for_you),
            "page_type": "lifestyle",
            "log_date": today.isoformat(),
            "responses": responses,
            "profile": _profile_dict(profile),
            "has_today_log": today_log is not None,
        },
    )


@router.post("/lifestyle")
async def lifestyle_checkin_submit(
    request: Request,
    background_tasks: BackgroundTasks,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(require_logged_in_user)],
    sleep_hours: Annotated[float, Form()],
    water_glasses: Annotated[int, Form()],
    activity_level: Annotated[str, Form()],
    screen_hours: Annotated[float, Form()],
    mood: Annotated[int, Form()],
    stress: Annotated[int, Form()],
    energy: Annotated[int, Form()],
    notes: Annotated[str, Form()] = "",
):
    try:
        activity = ActivityLevel(activity_level)
    except ValueError as exc:
        raise AppError("Invalid activity level", code="INVALID_ACTIVITY", status_code=400) from exc

    responses = {
        "sleep_hours": sleep_hours,
        "water_glasses": water_glasses,
        "activity_level": activity.value,
        "screen_hours": screen_hours,
        "mood": mood,
        "stress": stress,
        "energy": energy,
        "notes": notes.strip() or None,
    }

    _, _, material_change = await LifestyleService(db).upsert_daily_log(
        user.id,
        date.today(),
        responses,
    )

    set_flash(request, "Daily check-in saved.")
    if material_change:
        session_id = request.cookies.get(get_settings().ANON_SESSION_COOKIE_NAME)
        background_tasks.add_task(
            _trigger_recommendations_after_lifestyle,
            user.id,
            session_id,
            material_change,
            False,
        )

    return RedirectResponse(url="/lifestyle", status_code=303)
