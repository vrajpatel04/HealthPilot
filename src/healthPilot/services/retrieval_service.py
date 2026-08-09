from __future__ import annotations

from typing import Any

from healthPilot.core.config import get_settings
from healthPilot.models.enums import ProductCategory
from healthPilot.repositories.product_repository import ProductRepository
from healthPilot.vector.embedding_client import EmbeddingClient
from healthPilot.vector.qdrant_search import QdrantSearcher


class RetrievalService:
    def __init__(self, session, embedding_client: EmbeddingClient | None = None):
        self.session = session
        self.products = ProductRepository(session)
        self.embedding = embedding_client or EmbeddingClient()
        self.searcher = QdrantSearcher()

    def _product_dicts(self, products) -> list[dict[str, Any]]:
        return [
            {
                "product_id": str(p.id),
                "title": p.title,
                "description": p.description,
                "category": p.category.value,
                "price": float(p.price),
                "score": 0.5,
            }
            for p in products
        ]

    async def retrieve_products(
        self,
        query: str,
        limit: int = 5,
        *,
        category: str | None = None,
    ) -> list[dict[str, Any]]:
        try:
            vector = await self.embedding.embed_text(query)
            hits = await self.searcher.search_products(vector, limit=limit)
            if hits:
                return hits
        except Exception:
            pass

        if category:
            try:
                cat = ProductCategory(category)
                items, _ = await self.products.list_products(
                    is_active=True, category=cat, page_size=limit
                )
                if items:
                    return self._product_dicts(items)
            except ValueError:
                pass

        items, _ = await self.products.list_products(is_active=True, q=query, page_size=limit)
        if items:
            return self._product_dicts(items)

        items, _ = await self.products.list_products(is_active=True, page_size=limit)
        return self._product_dicts(items)

    async def retrieve_knowledge(self, query: str) -> list[dict[str, Any]]:
        settings = get_settings()
        try:
            vector = await self.embedding.embed_text(query)
            return await self.searcher.search_knowledge(vector, limit=settings.RAG_RETRIEVAL_K)
        except Exception:
            return []
