from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field

from healthPilot.models.enums import EventType

PRODUCT_INTERACTION_EVENT_TYPES: frozenset[EventType] = frozenset(
    {
        EventType.product_view,
        EventType.description_scroll,
        EventType.product_return,
        EventType.time_on_page,
    }
)


class EventIngestItem(BaseModel):
    event_type: EventType
    product_id: UUID | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime


class EventBatchRequest(BaseModel):
    events: list[EventIngestItem] = Field(min_length=1, max_length=50)


class EventBatchResponse(BaseModel):
    accepted: int


def batch_has_product_interaction(events: list[EventIngestItem]) -> bool:
    return any(event.event_type in PRODUCT_INTERACTION_EVENT_TYPES for event in events)
