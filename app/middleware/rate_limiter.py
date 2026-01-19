"""
Rate Limiting Middleware
Enforces tiered rate limits using sliding window algorithm.
"""
import time
from collections import defaultdict
from typing import Dict, Tuple
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from app.config import TIER_CONFIG
from app.schemas.errors import ErrorCodes, ERROR_STATUS_CODES


class RateLimitData:
    """Stores rate limit tracking data for an API key."""
    
    def __init__(self):
        self.minute_requests: list[float] = []  # Timestamps of requests in current minute
        self.day_requests: list[float] = []     # Timestamps of requests in current day
    
    def cleanup_old_requests(self):
        """Remove expired timestamps."""
        now = time.time()
        minute_ago = now - 60
        day_ago = now - 86400
        
        self.minute_requests = [t for t in self.minute_requests if t > minute_ago]
        self.day_requests = [t for t in self.day_requests if t > day_ago]
    
    def add_request(self):
        """Record a new request."""
        now = time.time()
        self.minute_requests.append(now)
        self.day_requests.append(now)
    
    def get_counts(self) -> Tuple[int, int]:
        """Get current request counts for minute and day."""
        self.cleanup_old_requests()
        return len(self.minute_requests), len(self.day_requests)


# In-memory storage for rate limit tracking
# In production, use Redis for distributed rate limiting
_rate_limit_store: Dict[str, RateLimitData] = defaultdict(RateLimitData)


class RateLimiterMiddleware(BaseHTTPMiddleware):
    """
    Middleware for tiered rate limiting.
    
    Enforces:
    - Per-minute rate limits based on tier
    - Per-day rate limits based on tier
    - Monthly quota tracking (handled by auth middleware)
    """
    
    async def dispatch(self, request: Request, call_next):
        # Skip rate limiting for public paths
        public_paths = {"/", "/health", "/docs", "/openapi.json", "/redoc"}
        if request.url.path in public_paths:
            return await call_next(request)
        
        # Skip for OPTIONS (CORS preflight)
        if request.method == "OPTIONS":
            return await call_next(request)
        
        # Get API key from request state (set by auth middleware)
        api_key = getattr(request.state, 'api_key', None)
        if not api_key:
            # Auth middleware will handle this
            return await call_next(request)
        
        # Get tier configuration
        tier = api_key.tier or "free"
        tier_config = TIER_CONFIG.get(tier, TIER_CONFIG["free"])
        
        # Get rate limit tracking data
        key_id = str(api_key.id)
        rate_data = _rate_limit_store[key_id]
        
        # Check rate limits
        minute_count, day_count = rate_data.get_counts()
        
        minute_limit = tier_config.get("rate_limit_per_minute", 10)
        day_limit = tier_config.get("rate_limit_per_day")
        
        # Check per-minute limit
        if minute_count >= minute_limit:
            return self._rate_limit_response(
                request.state.request_id,
                f"Rate limit exceeded: {minute_limit} requests per minute",
                retry_after=60
            )
        
        # Check per-day limit (if set)
        if day_limit and day_count >= day_limit:
            return self._rate_limit_response(
                request.state.request_id,
                f"Daily rate limit exceeded: {day_limit} requests per day",
                retry_after=3600
            )
        
        # Record this request
        rate_data.add_request()
        
        # Add rate limit headers to response
        response = await call_next(request)
        
        # Update counts after recording
        new_minute_count, new_day_count = rate_data.get_counts()
        
        response.headers["X-RateLimit-Limit-Minute"] = str(minute_limit)
        response.headers["X-RateLimit-Remaining-Minute"] = str(max(0, minute_limit - new_minute_count))
        if day_limit:
            response.headers["X-RateLimit-Limit-Day"] = str(day_limit)
            response.headers["X-RateLimit-Remaining-Day"] = str(max(0, day_limit - new_day_count))
        
        return response
    
    def _rate_limit_response(self, request_id: str, message: str, retry_after: int) -> JSONResponse:
        """Create rate limit error response."""
        return JSONResponse(
            status_code=429,
            content={
                "success": False,
                "request_id": request_id,
                "error": {
                    "code": ErrorCodes.RATE_LIMIT_EXCEEDED,
                    "message": message,
                    "billable": False
                }
            },
            headers={
                "X-Request-ID": request_id,
                "Retry-After": str(retry_after)
            }
        )


def get_rate_limit_status(api_key_id: str, tier: str = "free") -> dict:
    """
    Get current rate limit status for an API key.
    
    Returns:
        Dictionary with current usage and limits
    """
    tier_config = TIER_CONFIG.get(tier, TIER_CONFIG["free"])
    rate_data = _rate_limit_store.get(api_key_id, RateLimitData())
    
    minute_count, day_count = rate_data.get_counts()
    minute_limit = tier_config.get("rate_limit_per_minute", 10)
    day_limit = tier_config.get("rate_limit_per_day")
    
    return {
        "tier": tier,
        "minute": {
            "used": minute_count,
            "limit": minute_limit,
            "remaining": max(0, minute_limit - minute_count)
        },
        "day": {
            "used": day_count,
            "limit": day_limit,
            "remaining": max(0, day_limit - day_count) if day_limit else None
        }
    }
