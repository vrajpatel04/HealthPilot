import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from healthPilot.core.exceptions import AppError
from healthPilot.models.event import Event
from healthPilot.repositories.event_repository import EventRepository
from healthPilot.schemas.event import EventBatchRequest, EventBatchResponse, EventIngestItem


class EventService:
    MAX_FUTURE_SKEW = timedelta(minutes=5)

    def __init__(self, session: AsyncSession):
        self.session = session
        self.events = EventRepository(session)

    def _validate_timestamp(self, timestamp: datetime) -> None:
        now = datetime.now(timezone.utc)
        ts = timestamp if timestamp.tzinfo else timestamp.replace(tzinfo=timezone.utc)
        if ts > now + self.MAX_FUTURE_SKEW:
            raise AppError(
                "Event timestamp too far in the future",
                code="INVALID_TIMESTAMP",
                status_code=422,
            )

    def _to_model(
        self,
        item: EventIngestItem,
        *,
        session_id: str,
        user_id: uuid.UUID | None,
    ) -> Event:
        self._validate_timestamp(item.timestamp)
        ts = item.timestamp
        if ts.tzinfo is None:
            ts = ts.replace(tzinfo=timezone.utc)
        return Event(
            user_id=user_id,
            session_id=session_id,
            event_type=item.event_type,
            product_id=item.product_id,
            metadata_=item.metadata,
            timestamp=ts,
        )

    async def ingest_batch(
        self,
        payload: EventBatchRequest,
        *,
        session_id: str,
        user_id: uuid.UUID | None,
    ) -> EventBatchResponse:
        models = [
            self._to_model(item, session_id=session_id, user_id=user_id)
            for item in payload.events
        ]
        accepted = await self.events.bulk_create(models)
        await self.session.commit()
        return EventBatchResponse(accepted=accepted)
