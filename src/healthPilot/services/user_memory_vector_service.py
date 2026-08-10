from __future__ import annotations

import logging
import uuid
from typing import Any

from healthPilot.core.config import get_settings
from healthPilot.vector.embedding_client import EmbeddingClient
from healthPilot.vector.qdrant_user_memory import QdrantUserMemoryStore

logger = logging.getLogger(__name__)

_USER_MEMORY_NAMESPACE = uuid.UUID("6ba7b810-9dad-11d1-80b4-00c04fd430c8")


class UserMemoryVectorService:
    def __init__(
        self,
        store: QdrantUserMemoryStore | None = None,
        embedding: EmbeddingClient | None = None,
    ) -> None:
        self.settings = get_settings()
        self.store = store or QdrantUserMemoryStore()
        self.embedding = embedding or EmbeddingClient()

    @staticmethod
    def point_id(memory_type: str, source_id: str) -> uuid.UUID:
        return uuid.uuid5(_USER_MEMORY_NAMESPACE, f"{memory_type}:{source_id}")

    async def write_snippet(
        self,
        *,
        user_id: uuid.UUID,
        memory_type: str,
        source_id: str,
        text: str,
    ) -> None:
        try:
            vector = await self.embedding.embed_text(text)
            await self.store.upsert_snippet(
                point_id=self.point_id(memory_type, source_id),
                vector=vector,
                user_id=user_id,
                memory_type=memory_type,
                source_id=source_id,
                text=text,
            )
        except Exception as exc:
            logger.warning("Failed to write user memory snippet: %s", exc)

    async def search(self, user_id: uuid.UUID, query: str, limit: int | None = None) -> list[dict[str, Any]]:
        k = limit or self.settings.USER_MEMORY_RETRIEVAL_K
        try:
            vector = await self.embedding.embed_text(query)
            return await self.store.search(user_id=user_id, vector=vector, limit=k)
        except Exception as exc:
            logger.warning("Failed to search user memory: %s", exc)
            return []

    async def delete_by_source(self, user_id: uuid.UUID, source_id: str) -> None:
        try:
            await self.store.delete_by_source(user_id=user_id, source_id=source_id)
        except Exception as exc:
            logger.warning("Failed to delete user memory snippet: %s", exc)
