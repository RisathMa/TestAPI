"""
CRUD Operations
Database operations for API keys and usage logs.
"""
import secrets
from datetime import datetime
from typing import Optional
from sqlalchemy.orm import Session
from app.db.models import APIKey, UsageLog


# ============================================================================
# API Key Operations
# ============================================================================

def create_api_key(
    db: Session,
    name: str,
    tier: str = "free",
    monthly_limit: Optional[int] = 100
) -> APIKey:
    """
    Create a new API key with secure random generation.
    
    Args:
        db: Database session
        name: Friendly name for the key
        tier: Pricing tier (free, standard, enterprise)
        monthly_limit: Monthly request limit (None for unlimited)
    
    Returns:
        Created APIKey instance
    """
    # Generate secure API key: sk_live_ prefix + 32 random hex chars
    key = f"sk_live_{secrets.token_hex(16)}"
    
    api_key = APIKey(
        key=key,
        name=name,
        tier=tier,
        monthly_limit=monthly_limit
    )
    db.add(api_key)
    db.commit()
    db.refresh(api_key)
    return api_key


def get_api_key_by_key(db: Session, key: str) -> Optional[APIKey]:
    """Look up an API key by its value."""
    return db.query(APIKey).filter(APIKey.key == key).first()


def get_api_key_by_id(db: Session, key_id: int) -> Optional[APIKey]:
    """Look up an API key by its ID."""
    return db.query(APIKey).filter(APIKey.id == key_id).first()


def validate_api_key(db: Session, key: str) -> tuple[bool, Optional[APIKey], Optional[str]]:
    """
    Validate an API key for authentication.
    
    Returns:
        Tuple of (is_valid, api_key, error_message)
    """
    api_key = get_api_key_by_key(db, key)
    
    if not api_key:
        return False, None, "Invalid API key"
    
    if not api_key.is_active:
        return False, None, "API key is disabled"
    
    # Check monthly limit for free tier
    if api_key.monthly_limit is not None:
        if api_key.requests_this_month >= api_key.monthly_limit:
            return False, api_key, "Monthly request limit exceeded"
    
    return True, api_key, None


def increment_api_key_usage(db: Session, api_key: APIKey) -> None:
    """Increment the usage counter and update last_used timestamp."""
    api_key.requests_this_month += 1
    api_key.last_used_at = datetime.utcnow()
    db.commit()


# ============================================================================
# Usage Log Operations
# ============================================================================

def create_usage_log(
    db: Session,
    request_id: str,
    api_key_id: int,
    url: str,
    billable_units: int = 1,
    cost_usd: float = 0.0,
    content_size_kb: Optional[float] = None,
    output_size_kb: Optional[float] = None,
    processing_time_ms: Optional[int] = None,
    success: bool = True,
    error_code: Optional[str] = None
) -> UsageLog:
    """
    Create a usage log entry for a request.
    
    Args:
        db: Database session
        request_id: Unique request identifier
        api_key_id: Associated API key ID
        url: Extracted URL
        billable_units: Number of billable units
        cost_usd: Cost in USD
        content_size_kb: Input content size
        output_size_kb: Output content size
        processing_time_ms: Processing duration
        success: Whether extraction succeeded
        error_code: Error code if failed
    
    Returns:
        Created UsageLog instance
    """
    log = UsageLog(
        request_id=request_id,
        api_key_id=api_key_id,
        url=url,
        billable_units=billable_units,
        cost_usd=cost_usd,
        content_size_kb=content_size_kb,
        output_size_kb=output_size_kb,
        processing_time_ms=processing_time_ms,
        success=success,
        error_code=error_code
    )
    db.add(log)
    db.commit()
    db.refresh(log)
    return log


def get_usage_stats(db: Session, api_key_id: int) -> dict:
    """
    Get usage statistics for an API key.
    
    Returns:
        Dictionary with total_requests, successful_requests, total_cost
    """
    logs = db.query(UsageLog).filter(UsageLog.api_key_id == api_key_id).all()
    
    return {
        "total_requests": len(logs),
        "successful_requests": sum(1 for log in logs if log.success),
        "total_cost_usd": sum(log.cost_usd for log in logs)
    }
