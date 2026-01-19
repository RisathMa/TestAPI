"""
API v1 Router
Aggregates all v1 endpoints.
"""
from fastapi import APIRouter
from app.api.v1.extract import router as extract_router
from app.api.v1.account import router as account_router

# Create v1 router
router = APIRouter(prefix="/v1", tags=["v1"])

# Include endpoint routers
router.include_router(extract_router)
router.include_router(account_router)

