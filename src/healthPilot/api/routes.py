from fastapi import APIRouter

from healthPilot.api.endpoints import auth, events, privacy, products
from healthPilot.api.endpoints.admin import products as admin_products
from healthPilot.api.endpoints.admin import sync as admin_sync

v1_router = APIRouter(prefix="/v1")
v1_router.include_router(auth.router, prefix="/auth", tags=["auth"])
v1_router.include_router(products.router, prefix="/products", tags=["products"])
v1_router.include_router(events.router, prefix="/events", tags=["events"])
v1_router.include_router(admin_products.router, prefix="/admin/products", tags=["admin-products"])
v1_router.include_router(admin_sync.router, prefix="/admin/sync", tags=["admin-sync"])
v1_router.include_router(privacy.router, prefix="/privacy", tags=["privacy"])

router = APIRouter()
router.include_router(v1_router)
