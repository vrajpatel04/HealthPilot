from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from typing import Any

from qdrant_client import AsyncQdrantClient
from qdrant_client.http import models as qmodels

from healthPilot.core.config import get_settings

logger = logging.getLogger(__name__)


class QdrantUserMemoryStore:
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
        return self.settings.USER_MEMORY_COLLECTION

    async def ensure_collection(self, vector_size: int) -> None:
        collections = await self.client.get_collections()
        names = {collection.name for collection in collections.collections}
        if self.collection_name in names:
            return
        await self.client.create_collection(
            collection_name=self.collection_name,
            vectors_config=qmodels.VectorParams(size=vector_size, distance=qmodels.Distance.COSINE),
        )

    async def upsert_snippet(
        self,
        *,
        point_id: uuid.UUID,
        vector: list[float],
        user_id: uuid.UUID,
        memory_type: str,
        source_id: str,
        text: str,
    ) -> None:
        await self.ensure_collection(len(vector))
        await self.client.upsert(
            collection_name=self.collection_name,
            points=[
                qmodels.PointStruct(
                    id=str(point_id),
                    vector=vector,
                    payload={
                        "user_id": str(user_id),
                        "memory_type": memory_type,
                        "source_id": source_id,
                        "text": text,
                        "created_at": datetime.now(timezone.utc).isoformat(),
                    },
                )
            ],
        )

    async def search(self, *, user_id: uuid.UUID, vector: list[float], limit: int) -> list[dict[str, Any]]:
        response = await self.client.query_points(
            collection_name=self.collection_name,
            query=vector,
            limit=limit,
            query_filter=qmodels.Filter(
                must=[
                    qmodels.FieldCondition(
                        key="user_id",
                        match=qmodels.MatchValue(value=str(user_id)),
                    )
                ]
            ),
        )
        return [
            {
                "text": (point.payload or {}).get("text", ""),
                "memory_type": (point.payload or {}).get("memory_type", ""),
                "source_id": (point.payload or {}).get("source_id", ""),
                "score": float(point.score or 0),
            }
            for point in response.points
        ]

    async def delete_by_source(self, *, user_id: uuid.UUID, source_id: str) -> None:
        await self.client.delete(
            collection_name=self.collection_name,
            points_selector=qmodels.FilterSelector(
                filter=qmodels.Filter(
                    must=[
                        qmodels.FieldCondition(
                            key="user_id",
                            match=qmodels.MatchValue(value=str(user_id)),
                        ),
                        qmodels.FieldCondition(
                            key="source_id",
                            match=qmodels.MatchValue(value=source_id),
                        ),
                    ]
                )
            ),
        )

    async def close(self) -> None:
        if self._client is not None:
            await self._client.close()
            self._client = None
