import uuid
from datetime import datetime

from sqlalchemy import desc, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from healthPilot.models.recommendation import Recommendation


class RecommendationRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, rec: Recommendation) -> Recommendation:
        self.session.add(rec)
        await self.session.flush()
        await self.session.refresh(rec)
        return rec

    async def get_latest(
        self,
        *,
        session_id: str,
        user_id: uuid.UUID | None = None,
    ) -> Recommendation | None:
        filters = []
        if user_id:
            filters.append(or_(Recommendation.user_id == user_id, Recommendation.session_id == session_id))
        else:
            filters.append(Recommendation.session_id == session_id)

        result = await self.session.execute(
            select(Recommendation).where(*filters).order_by(desc(Recommendation.created_at)).limit(1)
        )
        return result.scalar_one_or_none()

    async def get_by_id(self, recommendation_id: uuid.UUID) -> Recommendation | None:
        return await self.session.get(Recommendation, recommendation_id)
