import uuid
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock

import pytest

from healthPilot.models.enums import ProductCategory, VectorSyncStatus
from healthPilot.models.product import Product
from healthPilot.services.vector_sync_service import VectorSyncService


@pytest.mark.asyncio
async def test_sync_product_marks_synced_on_success():
    session = AsyncMock()
    product = Product(
        id=uuid.uuid4(),
        title="Sleep Better",
        description="A structured program",
        category=ProductCategory.sleep,
        price=Decimal("499.00"),
        metadata_={},
        is_active=True,
        vector_sync_status=VectorSyncStatus.pending,
    )

    repo = MagicMock()
    repo.get_by_id = AsyncMock(return_value=product)
    repo.save = AsyncMock(return_value=product)

    embedding_client = MagicMock()
    embedding_client.embed_text = AsyncMock(return_value=[0.1, 0.2, 0.3])

    qdrant_store = MagicMock()
    qdrant_store.upsert_product = AsyncMock()

    service = VectorSyncService(session)
    service.products = repo
    service.embedding_client = embedding_client
    service.qdrant_store = qdrant_store

    await service.sync_product(product.id, force=True)

    assert product.vector_sync_status == VectorSyncStatus.synced
    assert product.last_sync_error is None
    assert product.sync_attempts() == 0
    qdrant_store.upsert_product.assert_awaited_once()
    session.commit.assert_awaited()


@pytest.mark.asyncio
async def test_sync_product_marks_failed_on_error():
    session = AsyncMock()
    product = Product(
        id=uuid.uuid4(),
        title="Sleep Better",
        description="A structured program",
        category=ProductCategory.sleep,
        price=Decimal("499.00"),
        metadata_={},
        is_active=True,
        vector_sync_status=VectorSyncStatus.pending,
    )

    repo = MagicMock()
    repo.get_by_id = AsyncMock(return_value=product)
    repo.save = AsyncMock(return_value=product)

    embedding_client = MagicMock()
    embedding_client.embed_text = AsyncMock(side_effect=RuntimeError("mesh down"))

    qdrant_store = MagicMock()

    service = VectorSyncService(session)
    service.products = repo
    service.embedding_client = embedding_client
    service.qdrant_store = qdrant_store

    await service.sync_product(product.id, force=True)

    assert product.vector_sync_status == VectorSyncStatus.failed
    assert product.last_sync_error == "mesh down"
    assert product.sync_attempts() == 1
