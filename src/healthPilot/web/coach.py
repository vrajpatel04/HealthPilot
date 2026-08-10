from __future__ import annotations

import re
from typing import Annotated, Any

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from sqlalchemy.ext.asyncio import AsyncSession

from healthPilot.core.database import get_db
from healthPilot.models.user import User
from healthPilot.services.blood_report_service import BloodReportService
from healthPilot.web.deps import get_optional_user, show_for_you_nav
from healthPilot.web.marketplace import _base_context
from healthPilot.web.templates_env import templates

router = APIRouter()

_BIOMARKER_ALIASES: dict[str, str] = {
    "hba1c": "hba1c",
    "hb a1c": "hba1c",
    "glycated hemoglobin": "hba1c",
    "vitamin d": "vitamin_d",
    "25-hydroxy": "vitamin_d",
    "ldl": "ldl",
    "hdl": "hdl",
    "triglycerides": "triglycerides",
}


def _normalize_biomarker_key(name: str) -> str:
    lowered = name.strip().lower()
    for pattern, key in _BIOMARKER_ALIASES.items():
        if pattern in lowered:
            return key
    slug = re.sub(r"[^a-z0-9]+", "_", lowered).strip("_")
    return slug or lowered


def _coach_biomarkers_from_summary(summary: dict[str, Any] | None) -> dict[str, float | int | str]:
    if not summary:
        return {}

    biomarkers: dict[str, float | int | str] = {}
    for item in summary.get("biomarkers") or []:
        if not isinstance(item, dict):
            continue
        raw_name = str(item.get("name") or "").strip()
        value = item.get("value")
        if not raw_name or value is None:
            continue

        key = _normalize_biomarker_key(raw_name)
        if isinstance(value, (int, float)):
            biomarkers[key] = value
            continue
        if isinstance(value, str):
            try:
                biomarkers[key] = float(value)
            except ValueError:
                biomarkers[key] = value
    return biomarkers


@router.get("/coach", response_class=HTMLResponse)
async def coach_chat_page(
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User | None, Depends(get_optional_user)],
):
    show_for_you = await show_for_you_nav(request, db, user)
    biomarkers: dict[str, float | int | str] = {}
    if user is not None:
        summary = await BloodReportService(db).get_summary_for_pipeline(user.id)
        biomarkers = _coach_biomarkers_from_summary(summary)

    return templates.TemplateResponse(
        request,
        "coach/chat.html",
        {
            **_base_context(request, user, show_for_you=show_for_you),
            "page_type": "coach",
            "biomarkers": biomarkers,
        },
    )
