import uuid

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from healthPilot.core.config import get_settings


class AnonSessionMiddleware(BaseHTTPMiddleware):
    """Set hp_anon_session cookie on HTML responses when missing."""

    async def dispatch(self, request: Request, call_next) -> Response:
        settings = get_settings()
        existing = request.cookies.get(settings.ANON_SESSION_COOKIE_NAME)
        response = await call_next(request)

        content_type = response.headers.get("content-type", "")
        if existing or "text/html" not in content_type:
            return response

        session_id = str(uuid.uuid4())
        response.set_cookie(
            key=settings.ANON_SESSION_COOKIE_NAME,
            value=session_id,
            max_age=settings.ANON_SESSION_MAX_AGE,
            httponly=True,
            samesite="lax",
            secure=False,
        )
        return response
