import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from healthPilot.models.enums import ProductCategory, VectorSyncStatus
from healthPilot.models.product import Product


class ProductRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, product_id: uuid.UUID) -> Product | None:
        return await self.session.get(Product, product_id)

    async def create(self, product: Product) -> Product:
        self.session.add(product)
        await self.session.flush()
        await self.session.refresh(product)
        return product

    async def list_products(
        self,
        *,
        category: ProductCategory | None = None,
        is_active: bool | None = True,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[Product], int]:
        query = select(Product)
        count_query = select(func.count()).select_from(Product)

        if category is not None:
            query = query.where(Product.category == category)
            count_query = count_query.where(Product.category == category)
        if is_active is not None:
            query = query.where(Product.is_active == is_active)
            count_query = count_query.where(Product.is_active == is_active)

        total = (await self.session.execute(count_query)).scalar_one()
        offset = (page - 1) * page_size
        result = await self.session.execute(
            query.order_by(Product.created_at.desc()).offset(offset).limit(page_size)
        )
        return list(result.scalars().all()), total

    async def list_pending_sync(self) -> list[Product]:
        result = await self.session.execute(
            select(Product).where(
                Product.vector_sync_status.in_(
                    [VectorSyncStatus.pending, VectorSyncStatus.failed]
                )
            )
        )
        return list(result.scalars().all())

    async def save(self, product: Product) -> Product:
        await self.session.flush()
        await self.session.refresh(product)
        return product

    async def delete_soft(self, product: Product) -> Product:
        product.is_active = False
        product.vector_sync_status = VectorSyncStatus.pending
        return await self.save(product)
