import uuid
from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Depends, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from healthPilot.core.config import get_settings
from healthPilot.core.database import AsyncSessionLocal, get_db
from healthPilot.core.exceptions import AppError
from healthPilot.schemas.event import EventBatchRequest, EventBatchResponse
from healthPilot.services.event_service import EventService
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


async def _trigger_recommendations(session_id: str, user_id: uuid.UUID | None) -> None:
    async with AsyncSessionLocal() as db:
        await RecommendationOrchestrator(db).maybe_trigger_after_events(
            session_id=session_id,
            user_id=user_id,
        )


@router.post("/batch", response_model=EventBatchResponse, status_code=status.HTTP_202_ACCEPTED)
async def ingest_events_batch(
    body: EventBatchRequest,
    request: Request,
    background_tasks: BackgroundTasks,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> EventBatchResponse:
    settings = get_settings()
    session_id = request.cookies.get(settings.ANON_SESSION_COOKIE_NAME)
    if not session_id:
        raise AppError(
            "Anonymous session cookie required",
            code="MISSING_SESSION",
            status_code=400,
        )

    user_id = _optional_user_id(request)
    response = await EventService(db).ingest_batch(
        body,
        session_id=session_id,
        user_id=user_id,
    )
    background_tasks.add_task(_trigger_recommendations, session_id, user_id)
    return response
