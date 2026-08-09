from __future__ import annotations

from typing import Any

from qdrant_client import AsyncQdrantClient
from qdrant_client.http import models as qmodels

from healthPilot.core.config import get_settings


class QdrantSearcher:
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

    async def _query(
        self,
        *,
        collection: str,
        vector: list[float],
        limit: int,
        active_only: bool = False,
    ) -> list[Any]:
        query_filter = None
        if active_only:
            query_filter = qmodels.Filter(
                must=[qmodels.FieldCondition(key="is_active", match=qmodels.MatchValue(value=True))]
            )
        response = await self.client.query_points(
            collection_name=collection,
            query=vector,
            limit=limit,
            query_filter=query_filter,
        )
        return list(response.points)

    async def search_products(self, vector: list[float], limit: int = 5) -> list[dict[str, Any]]:
        try:
            points = await self._query(
                collection=self.settings.PRODUCTS_COLLECTION,
                vector=vector,
                limit=limit,
                active_only=True,
            )
        except Exception:
            return []

        hits = []
        for point in points:
            payload = point.payload or {}
            if not payload.get("is_active", True):
                continue
            hits.append(
                {
                    "product_id": payload.get("product_id") or str(point.id),
                    "title": payload.get("title", ""),
                    "category": payload.get("category", ""),
                    "price": payload.get("price", 0),
                    "score": float(point.score or 0),
                }
            )
        return hits

    async def search_knowledge(self, vector: list[float], limit: int = 3) -> list[dict[str, Any]]:
        try:
            points = await self._query(
                collection=self.settings.KNOWLEDGE_COLLECTION,
                vector=vector,
                limit=limit,
            )
        except Exception:
            return []
        return [
            {
                "text": (point.payload or {}).get("text", ""),
                "source": (point.payload or {}).get("source", ""),
                "score": float(point.score or 0),
            }
            for point in points
        ]
