from __future__ import annotations

import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from healthPilot.agents.blood_report_agent import BloodReportAgent
from healthPilot.agents.llm_helper import run_user_facing_llm
from healthPilot.core.config import get_settings
from healthPilot.core.exceptions import AppError, NotFoundError
from healthPilot.models.blood_report import BloodReport
from healthPilot.models.enums import BloodReportStatus
from healthPilot.repositories.blood_report_repository import BloodReportRepository
from healthPilot.services.user_memory_vector_service import UserMemoryVectorService

_ALLOWED_MIME = {"application/pdf", "image/jpeg", "image/png"}


class BloodReportService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.repo = BloodReportRepository(session)
        self.settings = get_settings()
        self.agent = BloodReportAgent()

    async def get_summary_for_pipeline(self, user_id: uuid.UUID) -> dict[str, Any] | None:
        report = await self.repo.get_latest_completed(user_id)
        if report is None:
            return None
        data = report.extracted_data or {}
        return {
            "report_id": str(report.id),
            "biomarkers": data.get("biomarkers", []),
            "flags": data.get("flags", []),
            "report_date": data.get("report_date"),
        }

    async def upload(
        self, user_id: uuid.UUID, *, file_name: str, mime_type: str, file_bytes: bytes
    ) -> BloodReport:
        if mime_type not in _ALLOWED_MIME:
            raise AppError("Unsupported file type", code="INVALID_MIME", status_code=400)
        if len(file_bytes) > self.settings.BLOOD_REPORT_MAX_BYTES:
            raise AppError("File too large", code="FILE_TOO_LARGE", status_code=413)

        report_id = uuid.uuid4()
        upload_dir = Path(self.settings.BLOOD_REPORT_UPLOAD_DIR) / str(user_id)
        upload_dir.mkdir(parents=True, exist_ok=True)
        safe_name = Path(file_name).name
        file_path = upload_dir / f"{report_id}_{safe_name}"
        file_path.write_bytes(file_bytes)

        report = BloodReport(
            id=report_id,
            user_id=user_id,
            file_name=safe_name,
            file_path=str(file_path),
            mime_type=mime_type,
            status=BloodReportStatus.pending,
        )
        await self.repo.create(report)
        await self.session.commit()
        return report

    async def process_report(self, report_id: uuid.UUID, user_id: uuid.UUID) -> BloodReport:
        report = await self.repo.get_by_id(report_id, user_id)
        if report is None:
            raise NotFoundError("Blood report not found", code="REPORT_NOT_FOUND")

        report.status = BloodReportStatus.processing
        await self.session.commit()

        try:
            file_bytes = Path(report.file_path).read_bytes()
            extracted = await self.agent.extract_biomarkers(file_bytes, report.mime_type)
            if not extracted.get("biomarkers"):
                raise ValueError("No biomarkers detected in report")

            report.extracted_data = extracted
            report.status = BloodReportStatus.completed
            report.processed_at = datetime.now(timezone.utc)
            report.last_error = None
            await self.session.commit()

            snippet = self._build_memory_snippet(extracted)
            await UserMemoryVectorService().write_snippet(
                user_id=user_id,
                memory_type="blood_report",
                source_id=str(report.id),
                text=snippet,
            )
        except Exception as exc:
            report.status = BloodReportStatus.failed
            report.last_error = str(exc)[:500]
            await self.session.commit()

        return report

    async def generate_wellness_summary(self, report: BloodReport) -> str:
        if report.status != BloodReportStatus.completed:
            return ""
        prompt = self.agent.build_summary_prompt(report.extracted_data or {})
        return await run_user_facing_llm(prompt)

    async def delete(self, report_id: uuid.UUID, user_id: uuid.UUID) -> None:
        report = await self.repo.get_by_id(report_id, user_id)
        if report is None:
            raise NotFoundError("Blood report not found", code="REPORT_NOT_FOUND")
        path = Path(report.file_path)
        if path.exists():
            path.unlink()
        await UserMemoryVectorService().delete_by_source(
            user_id=user_id, source_id=str(report.id)
        )
        await self.repo.delete(report)
        await self.session.commit()

    @staticmethod
    def _build_memory_snippet(extracted: dict[str, Any]) -> str:
        biomarkers = extracted.get("biomarkers") or []
        flags = extracted.get("flags") or []
        parts: list[str] = []
        for item in biomarkers:
            if not isinstance(item, dict):
                continue
            name = item.get("name", "unknown")
            value = item.get("value", "")
            unit = item.get("unit", "")
            label = f"{name} {value}"
            if unit:
                label = f"{label} {unit}"
            parts.append(label.strip())
        flag_text = ", ".join(flags) if flags else "no flags"
        return f"Blood report: {', '.join(parts)}; flags: {flag_text}"
