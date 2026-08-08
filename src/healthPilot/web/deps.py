import uuid
from typing import Annotated

from fastapi import Depends, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession

from healthPilot.core.database import get_db
from healthPilot.models.enums import UserRole
from healthPilot.models.user import User
from healthPilot.repositories.user_repository import UserRepository


async def get_optional_user(
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> User | None:
    user_id_raw = request.session.get("user_id")
    if not user_id_raw:
        return None
    try:
        user_id = uuid.UUID(str(user_id_raw))
    except ValueError:
        return None
    return await UserRepository(db).get_by_id(user_id)


async def require_admin_web(
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> User:
    user = await get_optional_user(request, db)
    if user is None:
        request.session["flash"] = "Please log in as admin."
        return RedirectResponse(url="/login", status_code=303)  # type: ignore[return-value]
    if user.role != UserRole.admin:
        request.session["flash"] = "Admin access required."
        return RedirectResponse(url="/", status_code=303)  # type: ignore[return-value]
    return user


def pop_flash(request: Request) -> str | None:
    return request.session.pop("flash", None)
