from unittest.mock import AsyncMock, MagicMock

import pytest
from httpx import ASGITransport, AsyncClient

from healthPilot.main import app


@pytest.mark.asyncio
async def test_events_batch_requires_anon_cookie():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/events/batch",
            json={
                "events": [
                    {
                        "event_type": "page_view",
                        "metadata": {},
                        "timestamp": "2026-08-08T12:00:00Z",
                    }
                ]
            },
        )
    assert response.status_code == 400
    assert response.json()["code"] == "MISSING_SESSION"


@pytest.mark.asyncio
async def test_home_page_renders():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/")
    assert response.status_code == 200
    assert "HealthPilot" in response.text
    assert "hp_anon_session" in response.headers.get("set-cookie", "")
    assert "event-tracker.js" not in response.text


@pytest.mark.asyncio
async def test_coach_page_renders():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/coach")
    assert response.status_code == 200
    assert "Wellness Coach" in response.text
    assert "coach-chat.js" in response.text


@pytest.mark.asyncio
async def test_privacy_coach_api_route():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/privacy/coach",
            json={"message": "What helps with sleep?"},
        )
    assert response.status_code == 200
    payload = response.json()
    assert payload["response"]
    assert payload["deidentified_input"]
