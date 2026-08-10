import uuid
from datetime import date

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from healthPilot.models.lifestyle_daily_log import LifestyleDailyLog


class LifestyleRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_user_date(
        self, user_id: uuid.UUID, log_date: date
    ) -> LifestyleDailyLog | None:
        result = await self.session.execute(
            select(LifestyleDailyLog).where(
                LifestyleDailyLog.user_id == user_id,
                LifestyleDailyLog.log_date == log_date,
            )
        )
        return result.scalar_one_or_none()

    async def upsert(self, log: LifestyleDailyLog) -> LifestyleDailyLog:
        existing = await self.get_by_user_date(log.user_id, log.log_date)
        if existing:
            existing.responses = log.responses
            await self.session.flush()
            await self.session.refresh(existing)
            return existing
        self.session.add(log)
        await self.session.flush()
        await self.session.refresh(log)
        return log

    async def list_in_range(
        self, user_id: uuid.UUID, from_date: date, to_date: date
    ) -> list[LifestyleDailyLog]:
        result = await self.session.execute(
            select(LifestyleDailyLog)
            .where(
                LifestyleDailyLog.user_id == user_id,
                LifestyleDailyLog.log_date >= from_date,
                LifestyleDailyLog.log_date <= to_date,
            )
            .order_by(LifestyleDailyLog.log_date)
        )
        return list(result.scalars().all())
