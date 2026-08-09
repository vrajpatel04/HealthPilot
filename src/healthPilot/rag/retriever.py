"""Retrieve knowledge chunks from Qdrant."""

from __future__ import annotations

from healthPilot.core.config import get_settings
from healthPilot.vector.embedding_client import EmbeddingClient
from healthPilot.vector.qdrant_search import QdrantSearcher


class KnowledgeRetriever:
    def __init__(self) -> None:
        self.settings = get_settings()
        self.embedding = EmbeddingClient()
        self.searcher = QdrantSearcher()

    async def retrieve(self, query: str, limit: int | None = None) -> list[dict]:
        k = limit or self.settings.RAG_RETRIEVAL_K
        vector = await self.embedding.embed_text(query)
        return await self.searcher.search_knowledge(vector, limit=k)
