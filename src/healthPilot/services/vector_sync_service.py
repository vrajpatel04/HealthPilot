import uuid
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from healthPilot.core.config import get_settings
from healthPilot.core.exceptions import NotFoundError
from healthPilot.models.enums import VectorSyncStatus
from healthPilot.repositories.product_repository import ProductRepository
from healthPilot.schemas.product import SyncRetryResponse
from healthPilot.vector.embedding_client import EmbeddingClient
from healthPilot.vector.qdrant_client import QdrantProductStore


class VectorSyncService:
    def __init__(
        self,
        session: AsyncSession,
        *,
        embedding_client: EmbeddingClient | None = None,
        qdrant_store: QdrantProductStore | None = None,
    ):
        self.session = session
        self.products = ProductRepository(session)
        self.settings = get_settings()
        self.embedding_client = embedding_client or EmbeddingClient()
        self.qdrant_store = qdrant_store or QdrantProductStore()

    async def sync_product(self, product_id: uuid.UUID, *, force: bool = False) -> None:
        product = await self.products.get_by_id(product_id)
        if product is None:
            raise NotFoundError("Product not found", code="PRODUCT_NOT_FOUND")

        if not force:
            attempts = product.sync_attempts()
            if attempts >= self.settings.VECTOR_SYNC_MAX_ATTEMPTS:
                return

        try:
            if not product.is_active:
                await self.qdrant_store.delete_product(product.id)
                product.vector_sync_status = VectorSyncStatus.synced
                product.last_sync_error = None
                product.last_synced_at = datetime.now(timezone.utc)
                product.reset_sync_attempts()
            else:
                vector = await self.embedding_client.embed_text(product.embedding_text())
                await self.qdrant_store.upsert_product(product, vector)
                product.vector_sync_status = VectorSyncStatus.synced
                product.last_sync_error = None
                product.last_synced_at = datetime.now(timezone.utc)
                product.reset_sync_attempts()

            await self.products.save(product)
            await self.session.commit()
        except Exception as exc:
            product.vector_sync_status = VectorSyncStatus.failed
            product.last_sync_error = str(exc)
            product.set_sync_attempts(product.sync_attempts() + 1)
            await self.products.save(product)
            await self.session.commit()

    async def sweep_pending(self) -> SyncRetryResponse:
        pending = await self.products.list_pending_sync()
        synced = 0
        failed = 0

        for product in pending:
            before_status = product.vector_sync_status
            await self.sync_product(product.id, force=False)
            refreshed = await self.products.get_by_id(product.id)
            if refreshed and refreshed.vector_sync_status == VectorSyncStatus.synced:
                synced += 1
            elif before_status == VectorSyncStatus.failed or (
                refreshed and refreshed.vector_sync_status == VectorSyncStatus.failed
            ):
                failed += 1

        return SyncRetryResponse(
            attempted=len(pending),
            synced=synced,
            failed=failed,
        )

    async def health_ok(self) -> bool:
        return await self.qdrant_store.health_ok()
