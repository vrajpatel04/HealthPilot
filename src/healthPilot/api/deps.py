import uuid
from typing import Annotated

from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from healthPilot.core.database import get_db
from healthPilot.core.exceptions import AuthError, ForbiddenError
from healthPilot.models.enums import UserRole
from healthPilot.models.user import User
from healthPilot.repositories.user_repository import UserRepository


async def get_current_user(
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> User:
    user_id_raw = request.session.get("user_id")
    if not user_id_raw:
        raise AuthError("Not authenticated", code="NOT_AUTHENTICATED")

    try:
        user_id = uuid.UUID(str(user_id_raw))
    except ValueError as exc:
        raise AuthError("Session invalid", code="INVALID_SESSION") from exc

    user = await UserRepository(db).get_by_id(user_id)
    if user is None:
        request.session.clear()
        raise AuthError("Session invalid", code="INVALID_SESSION")
    return user


async def require_admin(user: Annotated[User, Depends(get_current_user)]) -> User:
    if user.role != UserRole.admin:
        raise ForbiddenError()
    return user
