from fastapi import APIRouter

from app.api import (
    audit,
    auth,
    customers,
    extraction,
    health,
    invoices,
    services,
    settings,
)


api_router = APIRouter(prefix="/api")

api_router.include_router(health.router)
api_router.include_router(auth.router)
api_router.include_router(extraction.router)
api_router.include_router(invoices.router)
api_router.include_router(services.router)
api_router.include_router(customers.router)
api_router.include_router(audit.router)
api_router.include_router(settings.router)