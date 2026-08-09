from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from healthPilot.core.config import get_settings
from healthPilot.core.database import get_db
from healthPilot.models.enums import ProductCategory
from healthPilot.schemas.product import ProductListResponse, ProductPublicResponse
from healthPilot.services.product_cache import (
    get_cached_product_detail,
    get_cached_product_list,
    set_cached_product_detail,
    set_cached_product_list,
)
from healthPilot.services.product_service import ProductService

router = APIRouter()


@router.get("/", response_model=ProductListResponse)
async def list_products(
    db: Annotated[AsyncSession, Depends(get_db)],
    category: ProductCategory | None = None,
    q: str | None = Query(default=None, min_length=1),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    is_active: bool = Query(default=True),
) -> ProductListResponse:
    cache_params = {
        "category": category.value if category else None,
        "q": q,
        "page": page,
        "page_size": page_size,
        "is_active": is_active,
    }
    if get_settings().REDIS_URL:
        cached = await get_cached_product_list(**cache_params)
        if cached:
            return ProductListResponse.model_validate(cached)

    items, total = await ProductService(db).list_public(
        category=category,
        q=q,
        is_active=is_active,
        page=page,
        page_size=page_size,
    )
    response = ProductListResponse(
        items=[ProductPublicResponse.model_validate(item) for item in items],
        total=total,
        page=page,
        page_size=page_size,
    )
    if get_settings().REDIS_URL:
        await set_cached_product_list(response.model_dump(mode="json"), **cache_params)
    return response


@router.get("/{product_id}", response_model=ProductPublicResponse)
async def get_product(
    product_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ProductPublicResponse:
    if get_settings().REDIS_URL:
        cached = await get_cached_product_detail(str(product_id))
        if cached:
            return ProductPublicResponse.model_validate(cached)

    product = await ProductService(db).get_public(product_id)
    response = ProductPublicResponse.model_validate(product)
    if get_settings().REDIS_URL:
        await set_cached_product_detail(str(product_id), response.model_dump(mode="json"))
    return response
