from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field

from healthPilot.models.enums import FeedbackAction


class ProductSummary(BaseModel):
    id: UUID
    title: str
    description: str
    category: str
    price: str


class RecommendationResponse(BaseModel):
    id: UUID
    primary_product: ProductSummary | None = None
    secondary_product: ProductSummary | None = None
    message: str = ""
    reason: str = ""
    confidence: float = 0.0
    why_recommended: list[str] = Field(default_factory=list)
    cached: bool = False
    created_at: datetime | None = None


class RecommendationRefreshResponse(BaseModel):
    recommendation: RecommendationResponse | None = None
    generated: bool = False


class FeedbackRequest(BaseModel):
    recommendation_id: UUID
    action: FeedbackAction
