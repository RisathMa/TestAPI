"""
Request Logging Middleware
Structured logging for all API requests with timing and metadata.
"""
import time
import logging
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

# Configure logger
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger("cleanreader")


class LoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware for structured request/response logging.
    
    Logs:
    - Request method and path
    - Response status code
    - Processing time
    - Request ID
    - API key identifier (masked)
    """
    
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        
        # Process request
        response = await call_next(request)
        
        # Calculate processing time
        process_time_ms = int((time.time() - start_time) * 1000)
        
        # Get request ID (set by auth middleware)
        request_id = getattr(request.state, 'request_id', 'unknown')
        
        # Get masked API key for logging
        api_key_id = getattr(request.state, 'api_key_id', None)
        api_key_display = f"key_{api_key_id}" if api_key_id else "public"
        
        # Log request
        log_data = {
            "request_id": request_id,
            "method": request.method,
            "path": request.url.path,
            "status": response.status_code,
            "duration_ms": process_time_ms,
            "api_key": api_key_display,
            "client_ip": request.client.host if request.client else "unknown"
        }
        
        # Log level based on status
        if response.status_code >= 500:
            logger.error(f"Request: {log_data}")
        elif response.status_code >= 400:
            logger.warning(f"Request: {log_data}")
        else:
            logger.info(f"Request: {log_data}")
        
        # Add timing header
        response.headers["X-Process-Time-Ms"] = str(process_time_ms)
        
        return response
