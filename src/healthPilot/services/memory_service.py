from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from healthPilot.models.user_memory import UserMemory
from healthPilot.repositories.user_memory_repository import UserMemoryRepository


class MemoryService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.repo = UserMemoryRepository(session)

    async def load(self, *, session_id: str, user_id: uuid.UUID | None) -> dict[str, Any]:
        memory = await self.repo.get_for_actor(session_id=session_id, user_id=user_id)
        if not memory:
            return {
                "primary_interest": None,
                "secondary_interest": None,
                "preferences": {},
                "successful_recommendations": [],
            }
        return {
            "primary_interest": memory.primary_interest,
            "secondary_interest": memory.secondary_interest,
            "preferences": memory.preferences or {},
            "successful_recommendations": memory.successful_recommendations or [],
        }

    async def update_from_behavior(
        self,
        *,
        session_id: str,
        user_id: uuid.UUID | None,
        behavior: dict[str, Any],
    ) -> dict[str, Any]:
        memory = await self.repo.get_for_actor(session_id=session_id, user_id=user_id)
        if memory is None:
            memory = UserMemory(session_id=session_id, user_id=user_id)
        memory.primary_interest = behavior.get("primary_interest")
        memory.secondary_interest = behavior.get("secondary_interest")
        memory.preferences = {
            **(memory.preferences or {}),
            "engagement": behavior.get("engagement"),
            "content_type": "structured_programs",
        }
        await self.repo.upsert(memory)
        await self.session.commit()
        return await self.load(session_id=session_id, user_id=user_id)
