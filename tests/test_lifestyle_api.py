from datetime import date

import pytest
from httpx import AsyncClient


def _daily_payload(log_date: str | None = None) -> dict:
    return {
        "log_date": log_date or date.today().isoformat(),
        "responses": {
            "sleep_hours": 7,
            "water_glasses": 8,
            "activity_level": "moderate",
            "screen_hours": 3,
            "mood": 4,
            "stress": 2,
            "energy": 4,
        },
    }


@pytest.mark.asyncio
async def test_lifestyle_daily_requires_auth(client: AsyncClient):
    resp = await client.post(
        "/api/v1/lifestyle/daily",
        json=_daily_payload("2026-08-09"),
    )
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_lifestyle_upsert_returns_profile(authenticated_client: AsyncClient):
    resp = await authenticated_client.post(
        "/api/v1/lifestyle/daily",
        json=_daily_payload(),
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "profile" in data
    assert data["profile"]["sleep_average"] in (7, 7.0, "7.0")
    assert data["profile"]["days_in_window"] == 1
    assert data["material_change"] is True
