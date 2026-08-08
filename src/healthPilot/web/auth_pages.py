from typing import Annotated

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession

from healthPilot.core.database import get_db
from healthPilot.core.exceptions import AppError, ConflictError
from healthPilot.models.user import User
from healthPilot.services.auth_service import AuthService
from healthPilot.web.deps import get_optional_user, pop_flash
from healthPilot.web.templates_env import CATEGORY_LABELS, category_choices, templates

router = APIRouter()


def _auth_context(request: Request, user: User | None, *, error: str | None = None) -> dict:
    return {
        "request": request,
        "user": user,
        "flash": pop_flash(request),
        "error": error,
        "track_events": False,
        "categories": category_choices(),
        "category_labels": CATEGORY_LABELS,
    }


@router.get("/login", response_class=HTMLResponse)
async def login_page(
    request: Request,
    user: Annotated[User | None, Depends(get_optional_user)],
):
    if user:
        return RedirectResponse(url="/products", status_code=303)
    return templates.TemplateResponse(
        request,
        "auth/login.html",
        _auth_context(request, user),
    )


@router.post("/login")
async def login_submit(
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
    email: Annotated[str, Form()],
    password: Annotated[str, Form()],
):
    user = await get_optional_user(request, db)
    try:
        authenticated = await AuthService(db).authenticate(email, password)
    except AppError:
        return templates.TemplateResponse(
            request,
            "auth/login.html",
            _auth_context(request, user, error="Invalid email or password."),
            status_code=401,
        )

    request.session["user_id"] = str(authenticated.id)
    request.session["role"] = authenticated.role.value
    return RedirectResponse(url="/products", status_code=303)


@router.get("/register", response_class=HTMLResponse)
async def register_page(
    request: Request,
    user: Annotated[User | None, Depends(get_optional_user)],
):
    if user:
        return RedirectResponse(url="/products", status_code=303)
    return templates.TemplateResponse(
        request,
        "auth/register.html",
        _auth_context(request, user),
    )


@router.post("/register")
async def register_submit(
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
    name: Annotated[str, Form()],
    email: Annotated[str, Form()],
    password: Annotated[str, Form()],
    user: Annotated[User | None, Depends(get_optional_user)],
):
    try:
        await AuthService(db).register(name, email, password)
    except ConflictError:
        return templates.TemplateResponse(
            request,
            "auth/register.html",
            _auth_context(request, user, error="Email already registered."),
            status_code=409,
        )
    request.session["flash"] = "Account created. Please log in."
    return RedirectResponse(url="/login", status_code=303)


@router.post("/logout")
async def logout(request: Request):
    request.session.clear()
    return RedirectResponse(url="/", status_code=303)
