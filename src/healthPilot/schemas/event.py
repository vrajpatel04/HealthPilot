from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field

from healthPilot.models.enums import EventType


class EventIngestItem(BaseModel):
    event_type: EventType
    product_id: UUID | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime


class EventBatchRequest(BaseModel):
    events: list[EventIngestItem] = Field(min_length=1, max_length=50)


class EventBatchResponse(BaseModel):
    accepted: int
