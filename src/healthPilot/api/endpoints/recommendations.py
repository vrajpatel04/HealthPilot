import uuid
from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Depends, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from healthPilot.core.config import get_settings
from healthPilot.core.database import get_db
from healthPilot.core.exceptions import AppError
from healthPilot.schemas.recommendation import (
    FeedbackRequest,
    RecommendationRefreshResponse,
    RecommendationResponse,
)
from healthPilot.services.recommendation_orchestrator import RecommendationOrchestrator

router = APIRouter()


def _optional_user_id(request: Request) -> uuid.UUID | None:
    user_id_raw = request.session.get("user_id")
    if not user_id_raw:
        return None
    try:
        return uuid.UUID(str(user_id_raw))
    except ValueError:
        return None


def _session_id(request: Request) -> str:
    settings = get_settings()
    session_id = request.cookies.get(settings.ANON_SESSION_COOKIE_NAME)
    if not session_id:
        raise AppError(
            "Anonymous session cookie required",
            code="MISSING_SESSION",
            status_code=400,
        )
    return session_id


@router.get("/", response_model=RecommendationResponse | None)
async def get_recommendation(
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> RecommendationResponse | None:
    payload = await RecommendationOrchestrator(db).get_latest(
        session_id=_session_id(request),
        user_id=_optional_user_id(request),
    )
    if not payload:
        return None
    return RecommendationResponse.model_validate(payload)


@router.post("/refresh", response_model=RecommendationRefreshResponse)
async def refresh_recommendation(
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> RecommendationRefreshResponse:
    payload = await RecommendationOrchestrator(db).run_pipeline(
        session_id=_session_id(request),
        user_id=_optional_user_id(request),
        manual=True,
        bypass_cooldown=True,
    )
    if not payload:
        return RecommendationRefreshResponse(recommendation=None, generated=False)
    return RecommendationRefreshResponse(
        recommendation=RecommendationResponse.model_validate(payload),
        generated=True,
    )


@router.post("/feedback", status_code=status.HTTP_204_NO_CONTENT)
async def record_feedback(
    body: FeedbackRequest,
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> None:
    await RecommendationOrchestrator(db).record_feedback(
        recommendation_id=body.recommendation_id,
        action=body.action,
        user_id=_optional_user_id(request),
    )
