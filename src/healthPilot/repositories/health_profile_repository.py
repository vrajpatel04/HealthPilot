import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from healthPilot.models.health_profile import HealthProfile


class HealthProfileRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_user_id(self, user_id: uuid.UUID) -> HealthProfile | None:
        result = await self.session.execute(
            select(HealthProfile).where(HealthProfile.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def upsert(self, profile: HealthProfile) -> HealthProfile:
        existing = await self.get_by_user_id(profile.user_id)
        if existing:
            existing.sleep_average = profile.sleep_average
            existing.water_average = profile.water_average
            existing.activity_average = profile.activity_average
            existing.screen_time_average = profile.screen_time_average
            existing.mood_average = profile.mood_average
            existing.stress_average = profile.stress_average
            existing.energy_average = profile.energy_average
            existing.metadata_ = profile.metadata_ or {}
            await self.session.flush()
            await self.session.refresh(existing)
            return existing
        self.session.add(profile)
        await self.session.flush()
        await self.session.refresh(profile)
        return profile
