import uuid
from datetime import datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import Boolean, DateTime, Enum, Numeric, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from healthPilot.models.base import Base
from healthPilot.models.enums import ProductCategory, VectorSyncStatus


class Product(Base):
    __tablename__ = "products"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    category: Mapped[ProductCategory] = mapped_column(
        Enum(ProductCategory, name="product_category", native_enum=True),
        nullable=False,
    )
    price: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    metadata_: Mapped[dict[str, Any]] = mapped_column("metadata", JSONB, default=dict)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    vector_sync_status: Mapped[VectorSyncStatus] = mapped_column(
        Enum(VectorSyncStatus, name="vector_sync_status", native_enum=True),
        nullable=False,
        default=VectorSyncStatus.pending,
    )
    last_sync_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    last_synced_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    def embedding_text(self) -> str:
        return f"{self.title}. {self.category.value}. {self.description}"

    def sync_attempts(self) -> int:
        value = self.metadata_.get("sync_attempts", 0)
        return int(value) if value else 0

    def set_sync_attempts(self, attempts: int) -> None:
        self.metadata_ = {**self.metadata_, "sync_attempts": attempts}

    def reset_sync_attempts(self) -> None:
        self.set_sync_attempts(0)
