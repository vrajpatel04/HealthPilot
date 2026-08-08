from fastapi import APIRouter
from sqlalchemy import text

from healthPilot.core.config import get_settings
from healthPilot.core.database import AsyncSessionLocal
from healthPilot.privacy import GuardrailsClient, PresidioClient
from healthPilot.vector.qdrant_client import QdrantProductStore

settings = get_settings()
router = APIRouter()


@router.get("/health")
async def health_check():
    presidio_ok = await PresidioClient().health_ok()
    nemo_ok = await GuardrailsClient().health_ok()
    qdrant_ok = await QdrantProductStore().health_ok()

    postgres_ok = False
    try:
        async with AsyncSessionLocal() as session:
            await session.execute(text("SELECT 1"))
        postgres_ok = True
    except Exception:
        postgres_ok = False

    components = {
        "postgres": postgres_ok,
        "qdrant": qdrant_ok,
        "presidio": presidio_ok,
        "nemo_guardrails": nemo_ok,
    }
    healthy = all(components.values())

    return {
        "status": "healthy" if healthy else "degraded",
        "version": settings.VERSION,
        "service": settings.PROJECT_NAME,
        "components": components,
    }


@router.get("/")
async def root():
    return {
        "message": "Welcome to HealthPilot API",
        "docs_url": "/docs",
        "redoc_url": "/redoc",
    }
