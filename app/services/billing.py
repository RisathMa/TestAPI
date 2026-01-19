"""
Billing Service
Centralized billing logic with tier management.
"""
from datetime import datetime
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.config import get_settings, TIER_CONFIG
from app.db.models import APIKey, UsageLog


settings = get_settings()


class BillingService:
    """
    Centralized billing and account management service.
    
    Features:
    - Cost calculation with tier discounts
    - Usage tracking and alerts
    - Account status and quota management
    """
    
    def __init__(self):
        self.base_price = settings.base_price
        self.large_page_price = settings.large_page_price
        self.image_price = settings.image_extraction_price
        self.pdf_price = settings.pdf_extraction_price
        self.max_content_kb = settings.max_content_size_kb
    
    def calculate_cost(
        self,
        content_size_kb: float,
        include_images: bool = False,
        is_pdf: bool = False,
        tier: str = "standard"
    ) -> tuple[int, float]:
        """
        Calculate billing units and cost based on request characteristics.
        
        Args:
            content_size_kb: Size of fetched content in KB
            include_images: Whether image extraction was requested
            is_pdf: Whether PDF extraction was requested
            tier: API key tier for discount calculation
        
        Returns:
            Tuple of (billable_units, cost_usd)
        """
        # Free tier never charges
        if tier == "free":
            return 1, 0.0
        
        # Base cost
        cost = self.base_price
        billable_units = 1
        
        # Large page surcharge
        if content_size_kb > self.max_content_kb:
            cost += self.large_page_price
        
        # Image extraction surcharge
        if include_images:
            cost += self.image_price
        
        # PDF extraction surcharge
        if is_pdf:
            cost += self.pdf_price
        
        # Apply tier discount
        tier_config = TIER_CONFIG.get(tier, TIER_CONFIG["standard"] if "standard" in TIER_CONFIG else {})
        discount = tier_config.get("discount", 1.0)
        cost *= discount
        
        return billable_units, round(cost, 6)
    
    def get_account_status(self, db: Session, api_key: APIKey) -> Dict[str, Any]:
        """
        Get comprehensive account status including usage and billing.
        
        Returns:
            Dictionary with account details, usage stats, and billing info
        """
        tier = api_key.tier or "free"
        tier_config = TIER_CONFIG.get(tier, TIER_CONFIG["free"])
        
        # Calculate usage percentage
        monthly_limit = api_key.monthly_limit or tier_config.get("monthly_limit")
        usage_percentage = None
        if monthly_limit:
            usage_percentage = round((api_key.requests_this_month / monthly_limit) * 100, 2)
        
        # Get billing totals for this month
        current_month_start = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        monthly_cost = db.query(func.sum(UsageLog.cost_usd)).filter(
            UsageLog.api_key_id == api_key.id,
            UsageLog.created_at >= current_month_start
        ).scalar() or 0.0
        
        # Check alert thresholds
        alerts = []
        if usage_percentage:
            if usage_percentage >= settings.alert_threshold_critical:
                alerts.append({
                    "level": "critical",
                    "message": "Monthly quota exceeded. Requests will be rejected."
                })
            elif usage_percentage >= settings.alert_threshold_warning:
                alerts.append({
                    "level": "warning", 
                    "message": f"Usage at {usage_percentage}% of monthly quota."
                })
        
        return {
            "account": {
                "key_id": api_key.id,
                "name": api_key.name,
                "tier": tier,
                "tier_name": tier_config.get("name", tier.capitalize()),
                "is_active": api_key.is_active,
                "created_at": api_key.created_at.isoformat() if api_key.created_at else None,
                "features": tier_config.get("features", [])
            },
            "usage": {
                "requests_this_month": api_key.requests_this_month,
                "monthly_limit": monthly_limit,
                "usage_percentage": usage_percentage,
                "remaining": max(0, monthly_limit - api_key.requests_this_month) if monthly_limit else None,
                "last_used_at": api_key.last_used_at.isoformat() if api_key.last_used_at else None
            },
            "billing": {
                "current_month_cost_usd": round(monthly_cost, 4),
                "price_per_request": self.base_price * tier_config.get("discount", 1.0),
                "tier_discount": f"{int((1 - tier_config.get('discount', 1.0)) * 100)}%"
            },
            "rate_limits": {
                "per_minute": tier_config.get("rate_limit_per_minute"),
                "per_day": tier_config.get("rate_limit_per_day")
            },
            "alerts": alerts
        }
    
    def get_usage_history(
        self,
        db: Session,
        api_key_id: int,
        limit: int = 100,
        offset: int = 0
    ) -> Dict[str, Any]:
        """
        Get detailed usage history for an API key.
        
        Returns:
            Dictionary with usage records and summary stats
        """
        # Get total count
        total_count = db.query(func.count(UsageLog.id)).filter(
            UsageLog.api_key_id == api_key_id
        ).scalar() or 0
        
        # Get paginated records
        logs = db.query(UsageLog).filter(
            UsageLog.api_key_id == api_key_id
        ).order_by(
            UsageLog.created_at.desc()
        ).offset(offset).limit(limit).all()
        
        # Calculate summary
        total_cost = db.query(func.sum(UsageLog.cost_usd)).filter(
            UsageLog.api_key_id == api_key_id
        ).scalar() or 0.0
        
        successful_count = db.query(func.count(UsageLog.id)).filter(
            UsageLog.api_key_id == api_key_id,
            UsageLog.success == True
        ).scalar() or 0
        
        return {
            "summary": {
                "total_requests": total_count,
                "successful_requests": successful_count,
                "failed_requests": total_count - successful_count,
                "total_cost_usd": round(total_cost, 4),
                "success_rate": round((successful_count / total_count * 100), 2) if total_count > 0 else 0
            },
            "pagination": {
                "total": total_count,
                "limit": limit,
                "offset": offset,
                "has_more": (offset + limit) < total_count
            },
            "records": [
                {
                    "request_id": log.request_id,
                    "url": log.url[:100] + "..." if len(log.url) > 100 else log.url,
                    "success": log.success,
                    "cost_usd": log.cost_usd,
                    "content_size_kb": log.content_size_kb,
                    "processing_time_ms": log.processing_time_ms,
                    "error_code": log.error_code,
                    "created_at": log.created_at.isoformat() if log.created_at else None
                }
                for log in logs
            ]
        }
    
    def get_tier_comparison(self) -> list[Dict[str, Any]]:
        """
        Get comparison of all available tiers for upgrade decisions.
        
        Returns:
            List of tier details for pricing page
        """
        return [
            {
                "tier": tier_key,
                "name": config.get("name"),
                "monthly_limit": config.get("monthly_limit"),
                "rate_limit_per_minute": config.get("rate_limit_per_minute"),
                "rate_limit_per_day": config.get("rate_limit_per_day"),
                "price_monthly": config.get("price_monthly"),
                "price_per_request": round(settings.base_price * config.get("discount", 1.0), 6),
                "discount": f"{int((1 - config.get('discount', 1.0)) * 100)}%",
                "features": config.get("features", [])
            }
            for tier_key, config in TIER_CONFIG.items()
        ]


# Singleton instance
_billing_service: Optional[BillingService] = None


def get_billing_service() -> BillingService:
    """Get singleton billing service instance."""
    global _billing_service
    if _billing_service is None:
        _billing_service = BillingService()
    return _billing_service
