from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from healthPilot.api.deps import require_admin
from healthPilot.core.database import get_db
from healthPilot.models.user import User
from healthPilot.schemas.product import ProductAdminResponse, SyncRetryResponse
from healthPilot.services.vector_sync_service import VectorSyncService

router = APIRouter()


@router.post("/retry", response_model=SyncRetryResponse)
async def retry_all_pending(
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(require_admin)],
) -> SyncRetryResponse:
    return await VectorSyncService(db).sweep_pending()


@router.post("/products/{product_id}", response_model=ProductAdminResponse)
async def retry_product_sync(
    product_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(require_admin)],
) -> ProductAdminResponse:
    from healthPilot.repositories.product_repository import ProductRepository

    sync_service = VectorSyncService(db)
    product_repo = ProductRepository(db)
    product = await product_repo.get_by_id(product_id)
    if product is None:
        from healthPilot.core.exceptions import NotFoundError

        raise NotFoundError("Product not found", code="PRODUCT_NOT_FOUND")

    product.reset_sync_attempts()
    await product_repo.save(product)
    await db.commit()
    await sync_service.sync_product(product_id, force=True)
    refreshed = await product_repo.get_by_id(product_id)
    return ProductAdminResponse.model_validate(refreshed)
