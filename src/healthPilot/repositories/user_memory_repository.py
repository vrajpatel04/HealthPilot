import uuid

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from healthPilot.models.user_memory import UserMemory


class UserMemoryRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_for_actor(
        self,
        *,
        session_id: str,
        user_id: uuid.UUID | None = None,
    ) -> UserMemory | None:
        if user_id:
            result = await self.session.execute(
                select(UserMemory).where(
                    or_(UserMemory.user_id == user_id, UserMemory.session_id == session_id)
                )
            )
        else:
            result = await self.session.execute(
                select(UserMemory).where(UserMemory.session_id == session_id)
            )
        return result.scalar_one_or_none()

    async def upsert(self, memory: UserMemory) -> UserMemory:
        existing = await self.get_for_actor(session_id=memory.session_id, user_id=memory.user_id)
        if existing and existing.id != memory.id:
            existing.primary_interest = memory.primary_interest
            existing.secondary_interest = memory.secondary_interest
            existing.preferences = memory.preferences or {}
            existing.successful_recommendations = memory.successful_recommendations or []
            existing.metadata_ = memory.metadata_ or {}
            await self.session.flush()
            await self.session.refresh(existing)
            return existing
        self.session.add(memory)
        await self.session.flush()
        await self.session.refresh(memory)
        return memory
