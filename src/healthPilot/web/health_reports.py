from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Depends, File, Request, UploadFile
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession

from healthPilot.core.database import get_db
from healthPilot.models.user import User
from healthPilot.services.blood_report_service import BloodReportService
from healthPilot.web.deps import pop_flash, require_logged_in_user, set_flash, show_for_you_nav
from healthPilot.web.marketplace import _base_context
from healthPilot.web.templates_env import templates

router = APIRouter()


@router.get("/health/reports", response_class=HTMLResponse)
async def health_reports_page(
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(require_logged_in_user)],
):
    show_for_you = await show_for_you_nav(request, db, user)
    reports = await BloodReportService(db).repo.list_for_user(user.id)
    return templates.TemplateResponse(
        request,
        "health/reports.html",
        {
            **_base_context(request, user, show_for_you=show_for_you),
            "page_type": "health_reports",
            "reports": reports,
        },
    )


@router.post("/health/reports")
async def health_reports_upload(
    request: Request,
    background_tasks: BackgroundTasks,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(require_logged_in_user)],
    file: Annotated[UploadFile, File()],
):
    content = await file.read()
    report = await BloodReportService(db).upload(
        user.id,
        file_name=file.filename or "report.pdf",
        mime_type=file.content_type or "application/pdf",
        file_bytes=content,
    )
    from healthPilot.api.endpoints.blood_reports import _process_and_trigger
    from healthPilot.core.config import get_settings

    session_id = request.cookies.get(get_settings().ANON_SESSION_COOKIE_NAME)
    background_tasks.add_task(_process_and_trigger, report.id, user.id, session_id)
    set_flash(request, "Report uploaded — processing in background.")
    return RedirectResponse(url="/health/reports", status_code=303)
