from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from healthPilot.api.deps import require_admin
from healthPilot.core.database import get_db
from healthPilot.models.enums import ProductCategory
from healthPilot.models.user import User
from healthPilot.schemas.product import (
    ProductAdminResponse,
    ProductCreateRequest,
    ProductListResponse,
    ProductUpdateRequest,
)
from healthPilot.services.product_service import ProductService

router = APIRouter()


@router.post("/", response_model=ProductAdminResponse, status_code=status.HTTP_201_CREATED)
async def create_product(
    body: ProductCreateRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(require_admin)],
) -> ProductAdminResponse:
    product = await ProductService(db).create(body)
    return ProductAdminResponse.model_validate(product)


@router.get("/", response_model=ProductListResponse)
async def list_products_admin(
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(require_admin)],
    category: ProductCategory | None = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    is_active: bool | None = Query(default=None),
) -> ProductListResponse:
    items, total = await ProductService(db).list_admin(
        category=category,
        is_active=is_active,
        page=page,
        page_size=page_size,
    )
    return ProductListResponse(
        items=[ProductAdminResponse.model_validate(item) for item in items],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/{product_id}", response_model=ProductAdminResponse)
async def get_product_admin(
    product_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(require_admin)],
) -> ProductAdminResponse:
    product = await ProductService(db).get_admin(product_id)
    return ProductAdminResponse.model_validate(product)


@router.put("/{product_id}", response_model=ProductAdminResponse)
async def replace_product(
    product_id: UUID,
    body: ProductCreateRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(require_admin)],
) -> ProductAdminResponse:
    update = ProductUpdateRequest(**body.model_dump())
    product = await ProductService(db).update(product_id, update, partial=False)
    return ProductAdminResponse.model_validate(product)


@router.patch("/{product_id}", response_model=ProductAdminResponse)
async def patch_product(
    product_id: UUID,
    body: ProductUpdateRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(require_admin)],
) -> ProductAdminResponse:
    product = await ProductService(db).update(product_id, body, partial=True)
    return ProductAdminResponse.model_validate(product)


@router.delete("/{product_id}", response_model=ProductAdminResponse)
async def delete_product(
    product_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(require_admin)],
) -> ProductAdminResponse:
    product = await ProductService(db).delete(product_id)
    return ProductAdminResponse.model_validate(product)
