"""Chunk and ingest wellness knowledge documents into Qdrant."""

from __future__ import annotations

import hashlib
import uuid
from pathlib import Path

from qdrant_client import AsyncQdrantClient
from qdrant_client.http import models as qmodels

from healthPilot.core.config import get_settings
from healthPilot.vector.embedding_client import EmbeddingClient


def chunk_text(text: str, chunk_size: int, overlap: int) -> list[str]:
    if not text.strip():
        return []
    chunks: list[str] = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunks.append(text[start:end].strip())
        if end >= len(text):
            break
        start = max(end - overlap, start + 1)
    return [c for c in chunks if c]


def chunk_id(source: str, index: int, content: str) -> str:
    digest = hashlib.sha256(f"{source}:{index}:{content[:80]}".encode()).hexdigest()
    return digest


async def ensure_knowledge_collection(client: AsyncQdrantClient, collection: str, dim: int) -> None:
    exists = await client.collection_exists(collection)
    if not exists:
        await client.create_collection(
            collection_name=collection,
            vectors_config=qmodels.VectorParams(size=dim, distance=qmodels.Distance.COSINE),
        )


async def ingest_markdown_dir(
    knowledge_dir: Path,
    *,
    embedding_client: EmbeddingClient | None = None,
) -> int:
    settings = get_settings()
    embedding = embedding_client or EmbeddingClient()
    client_kwargs: dict = {"url": settings.QDRANT_URL}
    if settings.QDRANT_API_KEY:
        client_kwargs["api_key"] = settings.QDRANT_API_KEY
    client = AsyncQdrantClient(**client_kwargs)

    sample = await embedding.embed_text("health wellness")
    await ensure_knowledge_collection(client, settings.KNOWLEDGE_COLLECTION, len(sample))

    upserted = 0
    for path in sorted(knowledge_dir.glob("*.md")):
        text = path.read_text(encoding="utf-8")
        chunks = chunk_text(text, settings.RAG_CHUNK_SIZE, settings.RAG_CHUNK_OVERLAP)
        for index, chunk in enumerate(chunks):
            cid = chunk_id(path.name, index, chunk)
            point_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, cid))
            existing = await client.retrieve(
                collection_name=settings.KNOWLEDGE_COLLECTION,
                ids=[point_id],
            )
            if existing:
                continue
            vector = await embedding.embed_text(chunk)
            await client.upsert(
                collection_name=settings.KNOWLEDGE_COLLECTION,
                points=[
                    qmodels.PointStruct(
                        id=point_id,
                        vector=vector,
                        payload={"text": chunk, "source": path.name, "chunk_index": index},
                    )
                ],
            )
            upserted += 1
    return upserted
