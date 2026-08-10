import uuid
from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Depends, File, Request, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from healthPilot.api.deps import get_current_user
from healthPilot.core.config import get_settings
from healthPilot.core.database import AsyncSessionLocal, get_db
from healthPilot.core.exceptions import NotFoundError
from healthPilot.models.enums import BloodReportStatus
from healthPilot.models.user import User
from healthPilot.schemas.blood_report import BloodReportListResponse, BloodReportSummary
from healthPilot.services.blood_report_service import BloodReportService
from healthPilot.services.recommendation_orchestrator import RecommendationOrchestrator

router = APIRouter()


async def _process_and_trigger(
    report_id: uuid.UUID, user_id: uuid.UUID, session_id: str | None
) -> None:
    async with AsyncSessionLocal() as db:
        service = BloodReportService(db)
        report = await service.process_report(report_id, user_id)
        if report.status == BloodReportStatus.completed and session_id:
            await RecommendationOrchestrator(db).run_pipeline(
                session_id=session_id,
                user_id=user_id,
                lifestyle_trigger=True,
            )


@router.post("/", status_code=202)
async def upload_blood_report(
    request: Request,
    background_tasks: BackgroundTasks,
    file: Annotated[UploadFile, File()],
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    content = await file.read()
    report = await BloodReportService(db).upload(
        current_user.id,
        file_name=file.filename or "report.pdf",
        mime_type=file.content_type or "application/pdf",
        file_bytes=content,
    )
    session_id = request.cookies.get(get_settings().ANON_SESSION_COOKIE_NAME)
    background_tasks.add_task(
        _process_and_trigger,
        report.id,
        current_user.id,
        session_id,
    )
    return {"id": str(report.id), "status": report.status.value}


@router.get("/", response_model=BloodReportListResponse)
async def list_blood_reports(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> BloodReportListResponse:
    reports = await BloodReportService(db).repo.list_for_user(current_user.id)
    return BloodReportListResponse(
        items=[
            BloodReportSummary(
                id=r.id,
                file_name=r.file_name,
                status=r.status,
                upload_date=r.upload_date,
                processed_at=r.processed_at,
                extracted_data=r.extracted_data if r.status == BloodReportStatus.completed else None,
            )
            for r in reports
        ]
    )


@router.get("/{report_id}", response_model=BloodReportSummary)
async def get_blood_report(
    report_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> BloodReportSummary:
    service = BloodReportService(db)
    report = await service.repo.get_by_id(report_id, current_user.id)
    if report is None:
        raise NotFoundError("Blood report not found", code="REPORT_NOT_FOUND")
    wellness_summary = None
    if report.status == BloodReportStatus.completed:
        wellness_summary = await service.generate_wellness_summary(report)
    return BloodReportSummary(
        id=report.id,
        file_name=report.file_name,
        status=report.status,
        upload_date=report.upload_date,
        processed_at=report.processed_at,
        extracted_data=report.extracted_data,
        wellness_summary=wellness_summary,
    )


@router.delete("/{report_id}", status_code=204)
async def delete_blood_report(
    report_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> None:
    await BloodReportService(db).delete(report_id, current_user.id)
