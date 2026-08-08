from decimal import Decimal, InvalidOperation
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession

from healthPilot.core.database import get_db
from healthPilot.core.exceptions import NotFoundError
from healthPilot.models.enums import ProductCategory
from healthPilot.models.user import User
from healthPilot.repositories.product_repository import ProductRepository
from healthPilot.schemas.product import ProductCreateRequest, ProductUpdateRequest
from healthPilot.services.product_service import ProductService
from healthPilot.services.vector_sync_service import VectorSyncService
from healthPilot.web.deps import pop_flash, require_admin_web
from healthPilot.web.templates_env import CATEGORY_LABELS, category_choices, templates

router = APIRouter(prefix="/admin")


def _admin_context(request: Request, user: User) -> dict:
    return {
        "request": request,
        "user": user,
        "flash": pop_flash(request),
        "categories": category_choices(),
        "category_labels": CATEGORY_LABELS,
        "track_events": False,
    }


@router.get("/products", response_class=HTMLResponse)
async def admin_products_list(
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(require_admin_web)],
):
    items, _ = await ProductService(db).list_admin(is_active=None, page_size=100)
    return templates.TemplateResponse(
        request,
        "admin/products_list.html",
        {**_admin_context(request, user), "products": items},
    )


@router.get("/products/new", response_class=HTMLResponse)
async def admin_product_new(
    request: Request,
    user: Annotated[User, Depends(require_admin_web)],
):
    return templates.TemplateResponse(
        request,
        "admin/product_form.html",
        {**_admin_context(request, user), "product": None, "error": None},
    )


@router.post("/products/new")
async def admin_product_create(
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(require_admin_web)],
    title: Annotated[str, Form()],
    description: Annotated[str, Form()],
    category: Annotated[str, Form()],
    price: Annotated[str, Form()],
):
    try:
        data = ProductCreateRequest(
            title=title,
            description=description,
            category=ProductCategory(category),
            price=Decimal(price),
        )
        await ProductService(db).create(data)
    except (ValueError, InvalidOperation):
        request.session["flash"] = "Invalid product data."
        return RedirectResponse(url="/admin/products/new", status_code=303)

    request.session["flash"] = f"Created “{title}”."
    return RedirectResponse(url="/admin/products", status_code=303)


@router.get("/products/{product_id}/edit", response_class=HTMLResponse)
async def admin_product_edit(
    product_id: UUID,
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(require_admin_web)],
):
    try:
        product = await ProductService(db).get_admin(product_id)
    except NotFoundError:
        request.session["flash"] = "Product not found."
        return RedirectResponse(url="/admin/products", status_code=303)

    return templates.TemplateResponse(
        request,
        "admin/product_form.html",
        {**_admin_context(request, user), "product": product, "error": None},
    )


@router.post("/products/{product_id}/edit")
async def admin_product_update(
    product_id: UUID,
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(require_admin_web)],
    title: Annotated[str, Form()],
    description: Annotated[str, Form()],
    category: Annotated[str, Form()],
    price: Annotated[str, Form()],
):
    try:
        data = ProductUpdateRequest(
            title=title,
            description=description,
            category=ProductCategory(category),
            price=Decimal(price),
        )
        await ProductService(db).update(product_id, data, partial=False)
    except (ValueError, InvalidOperation, NotFoundError):
        request.session["flash"] = "Update failed."
        return RedirectResponse(url=f"/admin/products/{product_id}/edit", status_code=303)

    request.session["flash"] = "Product updated."
    return RedirectResponse(url="/admin/products", status_code=303)


@router.post("/products/{product_id}/delete")
async def admin_product_delete(
    product_id: UUID,
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(require_admin_web)],
):
    try:
        await ProductService(db).delete(product_id)
        request.session["flash"] = "Product deactivated."
    except NotFoundError:
        request.session["flash"] = "Product not found."
    return RedirectResponse(url="/admin/products", status_code=303)


@router.post("/sync/retry")
async def admin_sync_retry(
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(require_admin_web)],
):
    result = await VectorSyncService(db).sweep_pending()
    request.session["flash"] = (
        f"Sync sweep: {result.synced} synced, {result.failed} failed "
        f"({result.attempted} attempted)."
    )
    return RedirectResponse(url="/admin/products", status_code=303)


@router.post("/sync/products/{product_id}")
async def admin_sync_product(
    product_id: UUID,
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(require_admin_web)],
):
    product_repo = ProductRepository(db)
    product = await product_repo.get_by_id(product_id)
    if product is None:
        request.session["flash"] = "Product not found."
        return RedirectResponse(url="/admin/products", status_code=303)

    product.reset_sync_attempts()
    await product_repo.save(product)
    await db.commit()
    await VectorSyncService(db).sync_product(product_id, force=True)
    request.session["flash"] = "Resync triggered."
    return RedirectResponse(url="/admin/products", status_code=303)
