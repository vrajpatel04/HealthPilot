from __future__ import annotations

import asyncio
import json
import re
from typing import Any

import anydoc
from anydoc import ConvertError

from healthPilot.agents.llm_helper import run_internal_llm

BiomarkerEntry = dict[str, Any]

_EXTRACTION_SYSTEM_PROMPT = (
    "You extract every lab test result from de-identified blood report markdown. "
    "Return only valid JSON with no markdown fences or commentary."
)

_EXTRACTION_USER_TEMPLATE = """Extract every lab test from this blood report markdown.

Return JSON only, matching this schema:
{{
  "biomarkers": [
    {{"name": "<test name as printed>", "value": <number or string>, "unit": "<unit or empty string>"}},
    ...
  ],
  "report_date": "<YYYY-MM-DD or null>"
}}

Rules:
- Include every test result found in the report (hematology, chemistry, lipids, hormones, etc.).
- Use the test name exactly as shown in the report.
- `value` must be the numeric result when available; use a string only for qualitative results (e.g. "Negative").
- `unit` is the measurement unit (e.g. "mg/dL", "%", "ng/mL"); use "" if not shown.
- Do not include patient names, addresses, IDs, phone numbers, or other PII.
- Do not diagnose or interpret clinical significance.

Report markdown:
{markdown}
"""


def _to_markdown_sync(file_bytes: bytes, mime_type: str) -> str:
    if mime_type == "application/pdf":
        return anydoc.to_markdown_bytes(file_bytes)
    if mime_type.startswith("image/"):
        raise ValueError(
            "Standalone image reports are not supported; upload a text-based PDF instead."
        )
    raise ValueError(f"Unsupported file type for extraction: {mime_type}")


async def _to_markdown(file_bytes: bytes, mime_type: str) -> str:
    try:
        return await asyncio.to_thread(_to_markdown_sync, file_bytes, mime_type)
    except ConvertError as exc:
        raise ValueError(f"Could not convert report to markdown: {exc}") from exc


def _normalize_test_name(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", name.lower()).strip()


def _coerce_value(raw: Any) -> int | float | str | None:
    if raw is None:
        return None
    if isinstance(raw, bool):
        return None
    if isinstance(raw, (int, float)):
        return float(raw)
    if isinstance(raw, str):
        stripped = raw.strip()
        if not stripped:
            return None
        try:
            return float(stripped.replace(",", ""))
        except ValueError:
            return stripped
    return None


def _parse_biomarker_entry(raw: Any) -> BiomarkerEntry | None:
    if not isinstance(raw, dict):
        return None
    name = raw.get("name") or raw.get("test_name") or raw.get("test")
    if not isinstance(name, str) or not name.strip():
        return None
    value = _coerce_value(raw.get("value") if "value" in raw else raw.get("test_value"))
    if value is None:
        return None
    unit = raw.get("unit") or raw.get("test_unit") or ""
    if unit is None:
        unit = ""
    if not isinstance(unit, str):
        unit = str(unit)
    return {"name": name.strip(), "value": value, "unit": unit.strip()}


def _parse_extraction_response(text: str) -> dict[str, Any]:
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned, flags=re.I)
        cleaned = re.sub(r"\s*```$", "", cleaned)
    data = json.loads(cleaned)
    if not isinstance(data, dict):
        raise ValueError("LLM extraction did not return a JSON object")

    raw_biomarkers = data.get("biomarkers") or data.get("tests") or []
    biomarkers: list[BiomarkerEntry] = []
    if isinstance(raw_biomarkers, list):
        for item in raw_biomarkers:
            entry = _parse_biomarker_entry(item)
            if entry is not None:
                biomarkers.append(entry)
    elif isinstance(raw_biomarkers, dict):
        for name, payload in raw_biomarkers.items():
            if isinstance(payload, dict):
                entry = _parse_biomarker_entry({"name": name, **payload})
            else:
                entry = _parse_biomarker_entry({"name": name, "value": payload, "unit": ""})
            if entry is not None:
                biomarkers.append(entry)

    report_date = data.get("report_date")
    if report_date is not None and not isinstance(report_date, str):
        report_date = None

    return {"biomarkers": biomarkers, "report_date": report_date}


def _find_numeric_value(biomarkers: list[BiomarkerEntry], *patterns: str) -> float | None:
    for item in biomarkers:
        name = _normalize_test_name(str(item.get("name", "")))
        if not any(pattern in name for pattern in patterns):
            continue
        value = item.get("value")
        if isinstance(value, (int, float)):
            return float(value)
        if isinstance(value, str):
            try:
                return float(value.replace(",", ""))
            except ValueError:
                continue
    return None


def _derive_flags(biomarkers: list[BiomarkerEntry]) -> list[str]:
    flags: list[str] = []
    vitamin_d = _find_numeric_value(biomarkers, "vitamin d", "25 oh", "25-hydroxy")
    if vitamin_d is not None and vitamin_d < 20:
        flags.append("vitamin_d_low")
    ldl = _find_numeric_value(biomarkers, "ldl")
    if ldl is not None and ldl >= 130:
        flags.append("ldl_elevated")
    hba1c = _find_numeric_value(biomarkers, "hba1c", "hb a1c", "glycated hemoglobin")
    if hba1c is not None and hba1c >= 5.7:
        flags.append("hba1c_elevated")
    return flags


class BloodReportAgent:
    """Extract structured biomarkers via anydoc → privacy-pipeline LLM (no raw markdown persisted)."""

    async def extract_biomarkers(self, file_bytes: bytes, mime_type: str) -> dict[str, Any]:
        markdown = await _to_markdown(file_bytes, mime_type)
        if not markdown.strip():
            return {
                "biomarkers": [],
                "flags": [],
                "report_date": None,
                "parse_note": "no_text_extracted",
            }

        prompt = _EXTRACTION_USER_TEMPLATE.format(markdown=markdown)
        llm_text = await run_internal_llm(prompt, system_prompt=_EXTRACTION_SYSTEM_PROMPT)
        parsed = _parse_extraction_response(llm_text)
        biomarkers: list[BiomarkerEntry] = parsed["biomarkers"]

        if not biomarkers:
            return {
                "biomarkers": [],
                "flags": [],
                "report_date": parsed.get("report_date"),
                "parse_note": "no_biomarkers_detected",
            }

        return {
            "biomarkers": biomarkers,
            "flags": _derive_flags(biomarkers),
            "report_date": parsed.get("report_date"),
        }

    def build_summary_prompt(self, extracted_data: dict[str, Any]) -> str:
        return (
            "Summarize these lab values for general wellness context only. "
            "Do not diagnose or prescribe. Encourage consulting a professional when values look concerning.\n"
            f"Data: {json.dumps(extracted_data.get('biomarkers', []))}"
        )
