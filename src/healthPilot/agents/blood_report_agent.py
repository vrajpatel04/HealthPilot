from __future__ import annotations

import json
import re
from io import BytesIO
from typing import Any

from pypdf import PdfReader


_BIOMARKER_PATTERNS: dict[str, re.Pattern[str]] = {
    "hba1c": re.compile(r"hba1c\s*[:=]?\s*(\d+\.?\d*)", re.I),
    "vitamin_d": re.compile(r"vitamin\s*d\s*[:=]?\s*(\d+\.?\d*)", re.I),
    "ldl": re.compile(r"\bldl\s*[:=]?\s*(\d+\.?\d*)", re.I),
    "hdl": re.compile(r"\bhdl\s*[:=]?\s*(\d+\.?\d*)", re.I),
    "triglycerides": re.compile(r"triglycerides?\s*[:=]?\s*(\d+\.?\d*)", re.I),
}


def _extract_text(file_bytes: bytes, mime_type: str) -> str:
    if mime_type == "application/pdf":
        reader = PdfReader(BytesIO(file_bytes))
        return "\n".join(page.extract_text() or "" for page in reader.pages)
    if mime_type.startswith("image/"):
        return ""
    return ""


def _parse_biomarkers(text: str) -> dict[str, float]:
    biomarkers: dict[str, float] = {}
    for key, pattern in _BIOMARKER_PATTERNS.items():
        match = pattern.search(text)
        if match:
            biomarkers[key] = float(match.group(1))
    return biomarkers


def _derive_flags(biomarkers: dict[str, float]) -> list[str]:
    flags: list[str] = []
    vitamin_d = biomarkers.get("vitamin_d")
    if vitamin_d is not None and vitamin_d < 20:
        flags.append("vitamin_d_low")
    ldl = biomarkers.get("ldl")
    if ldl is not None and ldl >= 130:
        flags.append("ldl_elevated")
    hba1c = biomarkers.get("hba1c")
    if hba1c is not None and hba1c >= 5.7:
        flags.append("hba1c_elevated")
    return flags


class BloodReportAgent:
    """Extract structured biomarkers from report files (internal — no raw OCR persisted)."""

    def extract_biomarkers(self, file_bytes: bytes, mime_type: str) -> dict[str, Any]:
        text = _extract_text(file_bytes, mime_type)
        biomarkers = _parse_biomarkers(text)
        if not biomarkers:
            return {
                "biomarkers": {},
                "flags": [],
                "report_date": None,
                "parse_note": "no_biomarkers_detected",
            }
        return {
            "biomarkers": biomarkers,
            "flags": _derive_flags(biomarkers),
            "report_date": None,
        }

    def build_summary_prompt(self, extracted_data: dict[str, Any]) -> str:
        return (
            "Summarize these lab values for general wellness context only. "
            "Do not diagnose or prescribe. Encourage consulting a professional when values look concerning.\n"
            f"Data: {json.dumps(extracted_data.get('biomarkers', {}))}"
        )
