from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import HTMLResponse
from sqlalchemy.ext.asyncio import AsyncSession

from healthPilot.core.config import get_settings
from healthPilot.core.database import get_db
from healthPilot.core.exceptions import NotFoundError
from healthPilot.models.enums import ProductCategory
from healthPilot.models.user import User
from healthPilot.services.product_service import ProductService
from healthPilot.services.recommendation_orchestrator import RecommendationOrchestrator
from healthPilot.web.deps import get_optional_user, pop_flash, show_for_you_nav
from healthPilot.web.templates_env import CATEGORY_LABELS, category_choices, templates

router = APIRouter()


def _base_context(
    request: Request,
    user: User | None,
    *,
    show_for_you: bool = False,
    track_events: bool = False,
) -> dict:
    return {
        "request": request,
        "user": user,
        "flash": pop_flash(request),
        "categories": category_choices(),
        "category_labels": CATEGORY_LABELS,
        "track_events": track_events,
        "show_for_you": show_for_you,
    }


@router.get("/", response_class=HTMLResponse)
async def home(
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User | None, Depends(get_optional_user)],
):
    settings = get_settings()
    session_id = request.cookies.get(settings.ANON_SESSION_COOKIE_NAME)
    recommendation = None
    show_for_you = await show_for_you_nav(request, db, user)
    if session_id:
        orchestrator = RecommendationOrchestrator(db)
        recommendation = await orchestrator.get_latest(
            session_id=session_id,
            user_id=user.id if user else None,
        )

    return templates.TemplateResponse(
        request,
        "marketplace/home.html",
        {
            **_base_context(request, user, show_for_you=show_for_you),
            "page_type": "home",
            "recommendation": recommendation,
            "show_for_you": show_for_you,
        },
    )


@router.get("/products", response_class=HTMLResponse)
async def products_list(
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User | None, Depends(get_optional_user)],
    category: ProductCategory | None = None,
    q: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
):
    items, total = await ProductService(db).list_public(
        category=category,
        q=q,
        page=page,
        page_size=12,
    )
    show_for_you = await show_for_you_nav(request, db, user)
    return templates.TemplateResponse(
        request,
        "marketplace/products.html",
        {
            **_base_context(request, user, show_for_you=show_for_you),
            "page_type": "products",
            "products": items,
            "total": total,
            "page": page,
            "selected_category": category,
            "q": q or "",
            "results_count": total,
        },
    )


@router.get("/products/{product_id}", response_class=HTMLResponse)
async def product_detail(
    product_id: UUID,
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User | None, Depends(get_optional_user)],
):
    try:
        product = await ProductService(db).get_public(product_id)
    except NotFoundError:
        return templates.TemplateResponse(
            request,
            "marketplace/not_found.html",
            {**_base_context(request, user, show_for_you=await show_for_you_nav(request, db, user)), "page_type": "not_found"},
            status_code=404,
        )

    show_for_you = await show_for_you_nav(request, db, user)
    return templates.TemplateResponse(
        request,
        "marketplace/product_detail.html",
        {
            **_base_context(request, user, show_for_you=show_for_you, track_events=True),
            "page_type": "product_detail",
            "product": product,
        },
    )
