from fastapi import APIRouter
from healthPilot.core.config import get_settings

settings = get_settings()

router = APIRouter()

@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "version": settings.VERSION,
        "service": settings.PROJECT_NAME
    }

@router.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Welcome to HealthPilot API",
        "docs_url": "/docs",
        "redoc_url": "/redoc"
    }



