from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from healthPilot.models.enums import BloodReportStatus


class BloodReportSummary(BaseModel):
    id: UUID
    file_name: str
    status: BloodReportStatus
    upload_date: datetime
    processed_at: datetime | None = None
    extracted_data: dict | None = None
    wellness_summary: str | None = None

    model_config = ConfigDict(from_attributes=True)


class BloodReportListResponse(BaseModel):
    items: list[BloodReportSummary]
