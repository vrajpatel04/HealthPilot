import uuid

import pytest
from httpx import ASGITransport, AsyncClient

from healthPilot.main import app


@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.fixture
async def authenticated_client(client: AsyncClient):
    email = f"test-{uuid.uuid4()}@example.com"
    password = "password123"
    await client.post(
        "/api/v1/auth/register",
        json={"name": "Test User", "email": email, "password": password},
    )
    await client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password},
    )
    yield client
