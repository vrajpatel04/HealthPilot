import hashlib
import json
import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession

from healthPilot.core.config import get_settings
from healthPilot.core.database import get_db
from healthPilot.models.enums import FeedbackAction
from healthPilot.models.user import User
from healthPilot.services.recommendation_orchestrator import RecommendationOrchestrator
from healthPilot.web.deps import get_optional_user, pop_flash, set_flash, show_for_you_nav
from healthPilot.web.templates_env import templates

router = APIRouter()


def _session_id(request: Request) -> str | None:
    return request.cookies.get(get_settings().ANON_SESSION_COOKIE_NAME)


@router.get("/recommendations", response_class=HTMLResponse)
async def recommendations_page(
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User | None, Depends(get_optional_user)],
):
    from healthPilot.web.marketplace import _base_context

    session_id = _session_id(request)
    recommendation = None
    if session_id:
        recommendation = await RecommendationOrchestrator(db).get_latest(
            session_id=session_id,
            user_id=user.id if user else None,
        )

    show_for_you = await show_for_you_nav(request, db, user)
    return templates.TemplateResponse(
        request,
        "marketplace/recommendations.html",
        {
            **_base_context(request, user, show_for_you=show_for_you),
            "page_type": "recommendations",
            "recommendation": recommendation,
        },
    )


@router.post("/recommendations/refresh")
async def refresh_recommendations(
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User | None, Depends(get_optional_user)],
):
    session_id = _session_id(request)
    if session_id:
        await RecommendationOrchestrator(db).run_pipeline(
            session_id=session_id,
            user_id=user.id if user else None,
            manual=True,
            bypass_cooldown=True,
        )
    set_flash(request, "Recommendations refreshed based on your latest activity.")
    return RedirectResponse(url="/recommendations", status_code=303)


@router.post("/recommendations/feedback")
async def recommendation_feedback(
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User | None, Depends(get_optional_user)],
    recommendation_id: uuid.UUID = Form(...),
    action: FeedbackAction = Form(...),
):
    await RecommendationOrchestrator(db).record_feedback(
        recommendation_id=recommendation_id,
        action=action,
        user_id=user.id if user else None,
    )
    set_flash(request, "Thanks for your feedback!")
    return RedirectResponse(url="/recommendations", status_code=303)
