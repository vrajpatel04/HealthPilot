from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from healthPilot.models.blood_report import BloodReport
from healthPilot.models.enums import BloodReportStatus


class BloodReportRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_latest_completed(self, user_id: uuid.UUID) -> BloodReport | None:
        result = await self.session.execute(
            select(BloodReport)
            .where(
                BloodReport.user_id == user_id,
                BloodReport.status == BloodReportStatus.completed,
            )
            .order_by(BloodReport.processed_at.desc().nullslast(), BloodReport.upload_date.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def get_by_id(self, report_id: uuid.UUID, user_id: uuid.UUID) -> BloodReport | None:
        result = await self.session.execute(
            select(BloodReport).where(
                BloodReport.id == report_id,
                BloodReport.user_id == user_id,
            )
        )
        return result.scalar_one_or_none()

    async def list_for_user(self, user_id: uuid.UUID) -> list[BloodReport]:
        result = await self.session.execute(
            select(BloodReport)
            .where(BloodReport.user_id == user_id)
            .order_by(BloodReport.upload_date.desc())
        )
        return list(result.scalars().all())

    async def create(self, report: BloodReport) -> BloodReport:
        self.session.add(report)
        await self.session.flush()
        return report

    async def delete(self, report: BloodReport) -> None:
        await self.session.delete(report)
        await self.session.flush()
