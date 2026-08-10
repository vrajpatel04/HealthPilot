from __future__ import annotations

import json
from unittest.mock import AsyncMock, patch

import pytest

from healthPilot.agents.blood_report_agent import (
    BloodReportAgent,
    _derive_flags,
    _parse_extraction_response,
)


def test_derive_flags_vitamin_d_low():
    biomarkers = [
        {"name": "Vitamin D (25-OH)", "value": 14, "unit": "ng/mL"},
        {"name": "LDL Cholesterol", "value": 100, "unit": "mg/dL"},
    ]
    flags = _derive_flags(biomarkers)
    assert "vitamin_d_low" in flags


def test_parse_extraction_response_from_json_list():
    payload = {
        "biomarkers": [
            {"name": "HbA1c", "value": 6.2, "unit": "%"},
            {"name": "Vitamin D", "value": 14, "unit": "ng/mL"},
            {"name": "LDL", "value": 162, "unit": "mg/dL"},
        ],
        "report_date": "2026-07-15",
    }
    parsed = _parse_extraction_response(json.dumps(payload))
    assert len(parsed["biomarkers"]) == 3
    assert parsed["biomarkers"][0]["name"] == "HbA1c"
    assert parsed["biomarkers"][0]["value"] == 6.2
    assert parsed["biomarkers"][0]["unit"] == "%"
    assert parsed["report_date"] == "2026-07-15"


def test_parse_extraction_response_strips_code_fence():
    text = '```json\n{"biomarkers": [{"name": "LDL", "value": 120, "unit": "mg/dL"}], "report_date": null}\n```'
    parsed = _parse_extraction_response(text)
    assert parsed["biomarkers"][0]["value"] == 120.0
    assert parsed["biomarkers"][0]["unit"] == "mg/dL"


def test_parse_extraction_response_accepts_legacy_dict_shape():
    payload = {
        "biomarkers": {
            "LDL": {"value": 120, "unit": "mg/dL"},
            "HbA1c": 6.1,
        }
    }
    parsed = _parse_extraction_response(json.dumps(payload))
    names = {item["name"] for item in parsed["biomarkers"]}
    assert names == {"LDL", "HbA1c"}


@pytest.mark.asyncio
async def test_extract_returns_empty_for_unsupported_image():
    agent = BloodReportAgent()
    with pytest.raises(ValueError, match="Standalone image"):
        await agent.extract_biomarkers(b"fake-image", "image/jpeg")


@pytest.mark.asyncio
async def test_extract_uses_anydoc_then_llm():
    agent = BloodReportAgent()
    markdown = "HbA1c: 6.2\nVitamin D: 14\nLDL: 162"
    llm_payload = {
        "biomarkers": [
            {"name": "HbA1c", "value": 6.2, "unit": "%"},
            {"name": "Vitamin D", "value": 14, "unit": "ng/mL"},
            {"name": "LDL", "value": 162, "unit": "mg/dL"},
            {"name": "Hemoglobin", "value": 13.5, "unit": "g/dL"},
        ],
        "report_date": "2026-07-15",
    }

    with (
        patch(
            "healthPilot.agents.blood_report_agent._to_markdown",
            new=AsyncMock(return_value=markdown),
        ),
        patch(
            "healthPilot.agents.blood_report_agent.run_internal_llm",
            new=AsyncMock(return_value=json.dumps(llm_payload)),
        ),
    ):
        result = await agent.extract_biomarkers(b"%PDF", "application/pdf")

    assert len(result["biomarkers"]) == 4
    assert result["biomarkers"][0]["name"] == "HbA1c"
    assert result["biomarkers"][2]["value"] == 162.0
    assert "vitamin_d_low" in result["flags"]
    assert result["report_date"] == "2026-07-15"


@pytest.mark.asyncio
async def test_extract_returns_empty_when_no_biomarkers_in_llm_response():
    agent = BloodReportAgent()
    llm_payload = {"biomarkers": [], "report_date": None}

    with (
        patch(
            "healthPilot.agents.blood_report_agent._to_markdown",
            new=AsyncMock(return_value="Patient report with no labs"),
        ),
        patch(
            "healthPilot.agents.blood_report_agent.run_internal_llm",
            new=AsyncMock(return_value=json.dumps(llm_payload)),
        ),
    ):
        result = await agent.extract_biomarkers(b"%PDF", "application/pdf")

    assert result["biomarkers"] == []
    assert result["parse_note"] == "no_biomarkers_detected"
