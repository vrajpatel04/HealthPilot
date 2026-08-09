import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from healthPilot.models.feedback import Feedback
from healthPilot.models.enums import FeedbackAction


class FeedbackRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(
        self,
        *,
        recommendation_id: uuid.UUID,
        action: FeedbackAction,
        user_id: uuid.UUID | None,
    ) -> Feedback:
        fb = Feedback(
            recommendation_id=recommendation_id,
            action=action,
            user_id=user_id,
        )
        self.session.add(fb)
        await self.session.flush()
        await self.session.refresh(fb)
        return fb
