from fastapi import APIRouter

from healthPilot.api.endpoints import privacy

router = APIRouter()

router.include_router(privacy.router)