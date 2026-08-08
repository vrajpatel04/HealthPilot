from sqlalchemy.ext.asyncio import AsyncSession

from healthPilot.models.event import Event


class EventRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def bulk_create(self, events: list[Event]) -> int:
        self.session.add_all(events)
        await self.session.flush()
        return len(events)
