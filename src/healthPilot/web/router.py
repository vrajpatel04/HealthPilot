from fastapi import APIRouter

from healthPilot.web import admin_pages, auth_pages, coach, health_reports, lifestyle, marketplace, recommendations

router = APIRouter()
router.include_router(coach.router, tags=["web-coach"])
router.include_router(marketplace.router, tags=["web-marketplace"])
router.include_router(recommendations.router, tags=["web-recommendations"])
router.include_router(lifestyle.router, tags=["web-lifestyle"])
router.include_router(health_reports.router, tags=["web-health-reports"])
router.include_router(auth_pages.router, tags=["web-auth"])
router.include_router(admin_pages.router, tags=["web-admin"])
