from fastapi import APIRouter

from healthPilot.web import admin_pages, auth_pages, marketplace

router = APIRouter()
router.include_router(marketplace.router, tags=["web-marketplace"])
router.include_router(auth_pages.router, tags=["web-auth"])
router.include_router(admin_pages.router, tags=["web-admin"])
