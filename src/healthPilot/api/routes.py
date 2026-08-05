from fastapi import APIRouter
from healthPilot.api.endpoints import general

router = APIRouter()

# Include routers from different endpoint modules

# router.include_router(general.router, tags=["general"])

# router.include_router(app.router, tags=["ragapp"])