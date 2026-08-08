import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from healthPilot.core.config import get_settings
from healthPilot.core.exceptions import NotFoundError, SyncError
from healthPilot.models.enums import VectorSyncStatus
from healthPilot.models.product import Product
from healthPilot.repositories.product_repository import ProductRepository
from healthPilot.schemas.product import ProductCreateRequest, ProductUpdateRequest
from healthPilot.services.vector_sync_service import VectorSyncService


class ProductService:
    EMBED_FIELDS = {"title", "description", "category"}

    def __init__(self, session: AsyncSession, sync_service: VectorSyncService | None = None):
        self.session = session
        self.products = ProductRepository(session)
        self.sync_service = sync_service or VectorSyncService(session)

    async def create(self, data: ProductCreateRequest) -> Product:
        product = Product(
            title=data.title,
            description=data.description,
            category=data.category,
            price=data.price,
            metadata_=data.metadata,
            vector_sync_status=VectorSyncStatus.pending,
        )
        product = await self.products.create(product)
        await self.session.commit()
        await self.sync_service.sync_product(product.id, force=True)
        refreshed = await self.products.get_by_id(product.id)
        if refreshed is None:
            raise NotFoundError("Product not found after create", code="PRODUCT_NOT_FOUND")
        return refreshed

    async def get_public(self, product_id: uuid.UUID) -> Product:
        product = await self.products.get_by_id(product_id)
        if product is None or not product.is_active:
            raise NotFoundError("Product not found", code="PRODUCT_NOT_FOUND")
        return product

    async def list_public(
        self,
        *,
        category=None,
        q: str | None = None,
        is_active: bool = True,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[Product], int]:
        return await self.products.list_products(
            category=category,
            q=q,
            is_active=is_active,
            page=page,
            page_size=page_size,
        )

    async def get_admin(self, product_id: uuid.UUID) -> Product:
        product = await self.products.get_by_id(product_id)
        if product is None:
            raise NotFoundError("Product not found", code="PRODUCT_NOT_FOUND")
        return product

    async def list_admin(
        self,
        *,
        category=None,
        q: str | None = None,
        is_active: bool | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[Product], int]:
        return await self.products.list_products(
            category=category,
            q=q,
            is_active=is_active,
            page=page,
            page_size=page_size,
        )

    async def update(
        self,
        product_id: uuid.UUID,
        data: ProductUpdateRequest,
        *,
        partial: bool,
    ) -> Product:
        product = await self.get_admin(product_id)
        updates = data.model_dump(exclude_unset=partial)
        embed_changed = bool(self.EMBED_FIELDS.intersection(updates.keys()))

        for field, value in updates.items():
            if field == "metadata" and value is not None:
                product.metadata_ = value
            elif hasattr(product, field if field != "metadata" else "metadata_"):
                setattr(product, field if field != "metadata" else "metadata_", value)

        if embed_changed or updates.get("is_active") is True:
            product.vector_sync_status = VectorSyncStatus.pending

        await self.products.save(product)
        await self.session.commit()

        if embed_changed or "is_active" in updates:
            await self.sync_service.sync_product(product.id, force=True)

        refreshed = await self.products.get_by_id(product.id)
        if refreshed is None:
            raise NotFoundError("Product not found after update", code="PRODUCT_NOT_FOUND")
        return refreshed

    async def delete(self, product_id: uuid.UUID) -> Product:
        product = await self.get_admin(product_id)
        product = await self.products.delete_soft(product)
        await self.session.commit()
        await self.sync_service.sync_product(product.id, force=True)
        refreshed = await self.products.get_by_id(product.id)
        if refreshed is None:
            raise NotFoundError("Product not found after delete", code="PRODUCT_NOT_FOUND")
        return refreshed
