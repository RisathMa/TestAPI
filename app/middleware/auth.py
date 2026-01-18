"""
API Key Authentication Middleware
Validates Bearer tokens and attaches API key info to request state.
"""
from fastapi import Request, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
from app.db.database import SessionLocal
from app.db.crud import validate_api_key
from app.schemas.errors import ErrorCodes, ERROR_STATUS_CODES
import uuid


# Paths that don't require authentication
PUBLIC_PATHS = {
    "/",
    "/health",
    "/docs",
    "/openapi.json",
    "/redoc",
}


class AuthMiddleware(BaseHTTPMiddleware):
    """
    Middleware for API key authentication.
    
    Validates Bearer token from Authorization header and attaches
    API key info to request state for downstream use.
    """
    
    async def dispatch(self, request: Request, call_next):
        # Generate request ID for tracking
        request_id = f"req_{uuid.uuid4().hex[:12]}"
        request.state.request_id = request_id
        
        # Skip auth for public paths
        if request.url.path in PUBLIC_PATHS:
            return await call_next(request)
        
        # Skip auth for OPTIONS (CORS preflight)
        if request.method == "OPTIONS":
            return await call_next(request)
        
        # Extract Authorization header
        auth_header = request.headers.get("Authorization")
        
        if not auth_header:
            return self._error_response(
                request_id,
                ErrorCodes.INVALID_API_KEY,
                "Missing Authorization header"
            )
        
        # Validate Bearer token format
        if not auth_header.startswith("Bearer "):
            return self._error_response(
                request_id,
                ErrorCodes.INVALID_API_KEY,
                "Invalid Authorization header format. Use: Bearer <api_key>"
            )
        
        api_key = auth_header[7:]  # Remove "Bearer " prefix
        
        # Validate API key against database
        db = SessionLocal()
        try:
            is_valid, api_key_obj, error_msg = validate_api_key(db, api_key)
            
            if not is_valid:
                error_code = ErrorCodes.INVALID_API_KEY
                if error_msg == "API key is disabled":
                    error_code = ErrorCodes.API_KEY_DISABLED
                elif error_msg == "Monthly request limit exceeded":
                    error_code = ErrorCodes.RATE_LIMIT_EXCEEDED
                
                return self._error_response(request_id, error_code, error_msg)
            
            # Attach API key info to request state
            request.state.api_key = api_key_obj
            request.state.api_key_id = api_key_obj.id
            
        finally:
            db.close()
        
        # Continue to route handler
        response = await call_next(request)
        
        # Add request ID to response headers
        response.headers["X-Request-ID"] = request_id
        
        return response
    
    def _error_response(self, request_id: str, code: str, message: str) -> JSONResponse:
        """Create standardized error response."""
        status_code = ERROR_STATUS_CODES.get(code, 500)
        return JSONResponse(
            status_code=status_code,
            content={
                "success": False,
                "request_id": request_id,
                "error": {
                    "code": code,
                    "message": message,
                    "billable": False
                }
            },
            headers={"X-Request-ID": request_id}
        )


# FastAPI security scheme for Swagger UI
bearer_scheme = HTTPBearer(
    scheme_name="API Key",
    description="Enter your API key (format: sk_live_xxxxx)"
)


async def get_api_key(credentials: HTTPAuthorizationCredentials = None):
    """Dependency for getting API key from request."""
    if not credentials:
        raise HTTPException(status_code=401, detail="Missing API key")
    return credentials.credentials
