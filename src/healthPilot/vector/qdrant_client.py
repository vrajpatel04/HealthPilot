import uuid
from datetime import datetime
from typing import Any

from qdrant_client import AsyncQdrantClient
from qdrant_client.http import models as qmodels

from healthPilot.core.config import get_settings
from healthPilot.core.exceptions import SyncError
from healthPilot.models.product import Product


class QdrantProductStore:
    def __init__(self) -> None:
        self.settings = get_settings()
        self._client: AsyncQdrantClient | None = None

    @property
    def client(self) -> AsyncQdrantClient:
        if self._client is None:
            kwargs: dict[str, Any] = {"url": self.settings.QDRANT_URL}
            if self.settings.QDRANT_API_KEY:
                kwargs["api_key"] = self.settings.QDRANT_API_KEY
            self._client = AsyncQdrantClient(**kwargs)
        return self._client

    @property
    def collection_name(self) -> str:
        return self.settings.PRODUCTS_COLLECTION

    async def health_ok(self) -> bool:
        try:
            await self.client.get_collections()
            return True
        except Exception:
            return False

    async def ensure_collection(self, vector_size: int) -> None:
        collections = await self.client.get_collections()
        names = {collection.name for collection in collections.collections}
        if self.collection_name in names:
            return

        await self.client.create_collection(
            collection_name=self.collection_name,
            vectors_config=qmodels.VectorParams(size=vector_size, distance=qmodels.Distance.COSINE),
        )

    async def upsert_product(self, product: Product, vector: list[float]) -> None:
        await self.ensure_collection(len(vector))
        payload = {
            "product_id": str(product.id),
            "title": product.title,
            "category": product.category.value,
            "price": float(product.price),
            "is_active": product.is_active,
            "updated_at": product.updated_at.isoformat()
            if isinstance(product.updated_at, datetime)
            else datetime.utcnow().isoformat(),
        }
        await self.client.upsert(
            collection_name=self.collection_name,
            points=[
                qmodels.PointStruct(
                    id=str(product.id),
                    vector=vector,
                    payload=payload,
                )
            ],
        )

    async def delete_product(self, product_id: uuid.UUID) -> None:
        await self.client.delete(
            collection_name=self.collection_name,
            points_selector=qmodels.PointIdsList(points=[str(product_id)]),
        )

    async def close(self) -> None:
        if self._client is not None:
            await self._client.close()
            self._client = None
