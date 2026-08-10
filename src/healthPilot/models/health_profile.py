import uuid
from datetime import datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import DateTime, ForeignKey, Numeric, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from healthPilot.models.base import Base


class HealthProfile(Base):
    __tablename__ = "health_profiles"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )
    sleep_average: Mapped[Decimal | None] = mapped_column(Numeric(4, 1), nullable=True)
    water_average: Mapped[Decimal | None] = mapped_column(Numeric(4, 1), nullable=True)
    activity_average: Mapped[Decimal | None] = mapped_column(Numeric(3, 2), nullable=True)
    screen_time_average: Mapped[Decimal | None] = mapped_column(Numeric(4, 1), nullable=True)
    mood_average: Mapped[Decimal | None] = mapped_column(Numeric(3, 2), nullable=True)
    stress_average: Mapped[Decimal | None] = mapped_column(Numeric(3, 2), nullable=True)
    energy_average: Mapped[Decimal | None] = mapped_column(Numeric(3, 2), nullable=True)
    metadata_: Mapped[dict[str, Any]] = mapped_column("metadata", JSONB, default=dict)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
