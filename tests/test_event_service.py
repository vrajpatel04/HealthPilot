from datetime import datetime, timedelta, timezone

import pytest

from healthPilot.core.exceptions import AppError
from healthPilot.models.enums import EventType
from healthPilot.schemas.event import EventBatchRequest, EventIngestItem
from healthPilot.services.event_service import EventService


def test_rejects_future_timestamp():
    service = EventService(session=None)  # type: ignore[arg-type]
    future = datetime.now(timezone.utc) + timedelta(minutes=10)
    item = EventIngestItem(
        event_type=EventType.page_view,
        metadata={},
        timestamp=future,
    )
    with pytest.raises(AppError) as exc:
        service._validate_timestamp(item.timestamp)
    assert exc.value.code == "INVALID_TIMESTAMP"


def test_accepts_current_timestamp():
    service = EventService(session=None)  # type: ignore[arg-type]
    service._validate_timestamp(datetime.now(timezone.utc))
