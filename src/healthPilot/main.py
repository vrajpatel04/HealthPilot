from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text
from starlette.middleware.sessions import SessionMiddleware

from healthPilot.api.endpoints.general import router as general_router
from healthPilot.api.routes import router as api_router
from healthPilot.core.config import get_settings
from healthPilot.core.database import AsyncSessionLocal, engine
from healthPilot.core.exceptions import AppError
from healthPilot.jobs.vector_sync_job import start_vector_sync_scheduler, stop_vector_sync_scheduler
from healthPilot.privacy import GuardrailsClient, PresidioClient
from healthPilot.services.auth_service import AuthService
from healthPilot.vector.qdrant_client import QdrantProductStore

settings = get_settings()


async def _postgres_health_ok() -> bool:
    try:
        async with AsyncSessionLocal() as session:
            await session.execute(text("SELECT 1"))
        return True
    except Exception:
        return False


@asynccontextmanager
async def lifespan(app: FastAPI):
    presidio_ok = await PresidioClient().health_ok()
    nemo_ok = await GuardrailsClient().health_ok()
    postgres_ok = await _postgres_health_ok()
    qdrant_ok = await QdrantProductStore().health_ok()

    print(
        f"Privacy pipeline — Presidio: {'ready' if presidio_ok else 'failed'}, "
        f"NeMo Guardrails: {'ready' if nemo_ok else 'failed'}"
    )
    print(f"Database — PostgreSQL: {'ready' if postgres_ok else 'failed'}")
    print(f"Vector store — Qdrant: {'ready' if qdrant_ok else 'failed'}")

    if postgres_ok:
        async with AsyncSessionLocal() as session:
            admin = await AuthService(session).ensure_admin_exists()
            if admin:
                print(f"Admin bootstrap — created admin user: {admin.email}")

    start_vector_sync_scheduler()

    if not nemo_ok:
        print("NeMo Guardrails failed to load — check NEMO_LLM_* in .env and logs above.")
    if not postgres_ok:
        print("PostgreSQL unavailable — check DATABASE_URL in .env.")

    yield

    stop_vector_sync_scheduler()
    await engine.dispose()
    await QdrantProductStore().close()
    print("Shutting down...")


def create_application() -> FastAPI:
    app = FastAPI(
        title=settings.PROJECT_NAME,
        description=settings.PROJECT_DESCRIPTION,
        version=settings.VERSION,
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
    )

    @app.exception_handler(AppError)
    async def app_error_handler(_request, exc: AppError):
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.message, "code": exc.code},
        )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.ALLOWED_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(
        SessionMiddleware,
        secret_key=settings.SESSION_SECRET,
        session_cookie=settings.SESSION_COOKIE_NAME,
        max_age=settings.SESSION_MAX_AGE,
        same_site="lax",
        https_only=False,
    )

    app.include_router(general_router, tags=["general"])
    app.include_router(api_router, prefix="/api")

    return app


app = create_application()
