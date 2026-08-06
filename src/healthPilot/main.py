from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from healthPilot.core.config import get_settings
from healthPilot.api.routes import router as api_router
from healthPilot.api.endpoints.general import router as general_router
from healthPilot.privacy import GuardrailsClient, PresidioClient

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifecycle events for the FastAPI application.
    This runs on startup and shutdown.
    """
    presidio_ok = await PresidioClient().health_ok()
    nemo_ok = await GuardrailsClient().health_ok()
    print(
        f"Privacy pipeline — Presidio: {'ready' if presidio_ok else 'failed'}, "
        f"NeMo Guardrails: {'ready' if nemo_ok else 'failed'}"
    )
    if not nemo_ok:
        print("NeMo Guardrails failed to load — check NEMO_LLM_* in .env and logs above.")
    yield
    print("Shutting down...")


def create_application() -> FastAPI:
    """
    Create and configure the FastAPI application.
    """
    app = FastAPI(
        title=settings.PROJECT_NAME,
        description=settings.PROJECT_DESCRIPTION,
        version=settings.VERSION,
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
    )

    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.ALLOWED_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Include general routes at root level
    app.include_router(general_router, tags=["general"])

    # Include API routes with /api prefix
    app.include_router(api_router, prefix="/api")

    return app


# Create the FastAPI application instance
app = create_application()
