"""
Account & Usage API Endpoints
Provides account status, usage statistics, and billing information.
"""
from fastapi import APIRouter, Request, Query
from app.db.database import SessionLocal
from app.services.billing import get_billing_service
from app.middleware.rate_limiter import get_rate_limit_status


router = APIRouter(tags=["account"])


@router.get("/account")
async def get_account(request: Request):
    """
    Get account details and tier information.
    
    Returns:
        Account details, usage stats, billing info, and any alerts
    """
    api_key = request.state.api_key
    billing_service = get_billing_service()
    
    db = SessionLocal()
    try:
        account_status = billing_service.get_account_status(db, api_key)
        
        # Add rate limit status
        rate_status = get_rate_limit_status(str(api_key.id), api_key.tier)
        account_status["rate_limit_status"] = rate_status
        
        return {
            "success": True,
            "request_id": request.state.request_id,
            "data": account_status
        }
    finally:
        db.close()


@router.get("/usage")
async def get_usage(request: Request):
    """
    Get current month's usage summary.
    
    Returns:
        Usage statistics and billing summary
    """
    api_key = request.state.api_key
    billing_service = get_billing_service()
    
    db = SessionLocal()
    try:
        account_status = billing_service.get_account_status(db, api_key)
        
        return {
            "success": True,
            "request_id": request.state.request_id,
            "data": {
                "usage": account_status["usage"],
                "billing": account_status["billing"],
                "alerts": account_status["alerts"]
            }
        }
    finally:
        db.close()


@router.get("/usage/history")
async def get_usage_history(
    request: Request,
    limit: int = Query(default=50, le=100, ge=1, description="Number of records to return"),
    offset: int = Query(default=0, ge=0, description="Number of records to skip")
):
    """
    Get detailed usage history.
    
    Returns:
        Paginated list of usage records with summary statistics
    """
    api_key = request.state.api_key
    billing_service = get_billing_service()
    
    db = SessionLocal()
    try:
        history = billing_service.get_usage_history(
            db,
            api_key.id,
            limit=limit,
            offset=offset
        )
        
        return {
            "success": True,
            "request_id": request.state.request_id,
            "data": history
        }
    finally:
        db.close()


@router.get("/tiers")
async def get_tiers(request: Request):
    """
    Get available pricing tiers for comparison.
    
    This endpoint is useful for displaying upgrade options
    or for third-party integrations.
    
    Returns:
        List of all available tiers with pricing and features
    """
    billing_service = get_billing_service()
    tiers = billing_service.get_tier_comparison()
    
    return {
        "success": True,
        "request_id": request.state.request_id,
        "data": {
            "tiers": tiers,
            "current_tier": request.state.api_key.tier
        }
    }
