import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import desc, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from healthPilot.models.event import Event
from healthPilot.models.enums import EventType


class EventRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def bulk_create(self, events: list[Event]) -> int:
        self.session.add_all(events)
        await self.session.flush()
        return len(events)

    async def list_recent(
        self,
        *,
        session_id: str,
        user_id: uuid.UUID | None = None,
        hours: int = 168,
        limit: int = 200,
        event_types: frozenset[EventType] | None = None,
    ) -> list[Event]:
        since = datetime.now(timezone.utc) - timedelta(hours=hours)
        filters = [Event.timestamp >= since]
        if user_id:
            filters.append(or_(Event.user_id == user_id, Event.session_id == session_id))
        else:
            filters.append(Event.session_id == session_id)
        if event_types:
            filters.append(Event.event_type.in_(event_types))

        result = await self.session.execute(
            select(Event).where(*filters).order_by(desc(Event.timestamp)).limit(limit)
        )
        events = list(result.scalars().all())
        return list(reversed(events))
