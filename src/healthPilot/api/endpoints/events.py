import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from healthPilot.core.config import get_settings
from healthPilot.core.database import get_db
from healthPilot.core.exceptions import AppError
from healthPilot.schemas.event import EventBatchRequest, EventBatchResponse
from healthPilot.services.event_service import EventService

router = APIRouter()


def _optional_user_id(request: Request) -> uuid.UUID | None:
    user_id_raw = request.session.get("user_id")
    if not user_id_raw:
        return None
    try:
        return uuid.UUID(str(user_id_raw))
    except ValueError:
        return None


@router.post("/batch", response_model=EventBatchResponse, status_code=status.HTTP_202_ACCEPTED)
async def ingest_events_batch(
    body: EventBatchRequest,
    request: Request,
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

    return await EventService(db).ingest_batch(
        body,
        session_id=session_id,
        user_id=_optional_user_id(request),
    )
