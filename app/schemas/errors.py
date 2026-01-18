"""
Error Schemas
Standardized error response models.
"""
from typing import Literal, Optional
from pydantic import BaseModel, Field


class ErrorDetail(BaseModel):
    """Error detail information."""
    code: str = Field(description="Machine-readable error code")
    message: str = Field(description="Human-readable error message")
    billable: bool = Field(
        default=False,
        description="Whether this error should be billed"
    )


class ExtractErrorResponse(BaseModel):
    """Error response for extraction failures."""
    success: Literal[False] = False
    request_id: str = Field(description="Unique request identifier")
    error: ErrorDetail

    class Config:
        json_schema_extra = {
            "example": {
                "success": False,
                "request_id": "req_abc456",
                "error": {
                    "code": "FETCH_TIMEOUT",
                    "message": "Target URL took >5s to respond",
                    "billable": False
                }
            }
        }


# ============================================================================
# Error Codes
# ============================================================================

class ErrorCodes:
    """Standard error codes for the API."""
    
    # Authentication errors
    INVALID_API_KEY = "INVALID_API_KEY"
    API_KEY_DISABLED = "API_KEY_DISABLED"
    RATE_LIMIT_EXCEEDED = "RATE_LIMIT_EXCEEDED"
    
    # Fetch errors
    FETCH_TIMEOUT = "FETCH_TIMEOUT"
    FETCH_FAILED = "FETCH_FAILED"
    INVALID_URL = "INVALID_URL"
    URL_BLOCKED = "URL_BLOCKED"
    
    # Content errors
    CONTENT_TOO_LARGE = "CONTENT_TOO_LARGE"
    NO_CONTENT = "NO_CONTENT"
    EXTRACTION_FAILED = "EXTRACTION_FAILED"
    
    # Server errors
    INTERNAL_ERROR = "INTERNAL_ERROR"


# Error code to HTTP status mapping
ERROR_STATUS_CODES = {
    ErrorCodes.INVALID_API_KEY: 401,
    ErrorCodes.API_KEY_DISABLED: 403,
    ErrorCodes.RATE_LIMIT_EXCEEDED: 429,
    ErrorCodes.FETCH_TIMEOUT: 504,
    ErrorCodes.FETCH_FAILED: 502,
    ErrorCodes.INVALID_URL: 400,
    ErrorCodes.URL_BLOCKED: 403,
    ErrorCodes.CONTENT_TOO_LARGE: 413,
    ErrorCodes.NO_CONTENT: 422,
    ErrorCodes.EXTRACTION_FAILED: 422,
    ErrorCodes.INTERNAL_ERROR: 500,
}
