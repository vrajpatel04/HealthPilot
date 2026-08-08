from datetime import datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from healthPilot.models.enums import ProductCategory, VectorSyncStatus


class ProductCreateRequest(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    description: str = Field(min_length=1)
    category: ProductCategory
    price: Decimal = Field(gt=0, decimal_places=2)
    metadata: dict[str, Any] = Field(default_factory=dict)


class ProductUpdateRequest(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = Field(default=None, min_length=1)
    category: ProductCategory | None = None
    price: Decimal | None = Field(default=None, gt=0, decimal_places=2)
    metadata: dict[str, Any] | None = None
    is_active: bool | None = None


class ProductPublicResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: UUID
    title: str
    description: str
    category: ProductCategory
    price: Decimal
    metadata: dict[str, Any] = Field(validation_alias="metadata_")
    is_active: bool
    created_at: datetime
    updated_at: datetime


class ProductAdminResponse(ProductPublicResponse):
    vector_sync_status: VectorSyncStatus
    last_sync_error: str | None
    last_synced_at: datetime | None


class ProductListResponse(BaseModel):
    items: list[ProductPublicResponse] | list[ProductAdminResponse]
    total: int
    page: int
    page_size: int


class SyncRetryResponse(BaseModel):
    attempted: int
    synced: int
    failed: int
