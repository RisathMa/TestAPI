"""
Clean Reader API
Production-ready FastAPI service for URL content extraction.

Main application entry point with middleware registration and route setup.
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.db.database import init_db, SessionLocal
from app.db.crud import create_api_key, get_api_key_by_key
from app.api.v1.router import router as v1_router
from app.middleware.auth import AuthMiddleware
from app.middleware.logging import LoggingMiddleware
from app.middleware.rate_limiter import RateLimiterMiddleware

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager.
    Handles startup and shutdown events.
    """
    # Startup: Initialize database
    init_db()
    
    # Create demo API key if it doesn't exist
    db = SessionLocal()
    try:
        if not get_api_key_by_key(db, "sk_test_demo_key"):
            create_api_key(
                db,
                name="Demo Key",
                tier="standard",
                monthly_limit=1000
            )
            # Update the key to use our demo key for testing
            demo_key = get_api_key_by_key(db, db.query(
                __import__('app.db.models', fromlist=['APIKey']).APIKey
            ).first().key)
            if demo_key:
                demo_key.key = "sk_test_demo_key"
                db.commit()
    except Exception:
        # If demo key creation fails, create it directly
        db.rollback()
        from app.db.models import APIKey
        existing = db.query(APIKey).filter(APIKey.key == "sk_test_demo_key").first()
        if not existing:
            new_key = APIKey(
                key="sk_test_demo_key",
                name="Demo Key",
                tier="standard",
                monthly_limit=1000
            )
            db.add(new_key)
            db.commit()
    finally:
        db.close()
    
    yield
    
    # Shutdown: Cleanup resources if needed
    pass


# Create FastAPI application
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="""
## Clean Reader API

Convert any web URL into clean, LLM-optimized Markdown with intelligent content extraction.

### Features

- **Content Extraction**: Uses Mozilla Readability algorithm to extract main article content
- **Markdown Conversion**: Clean, structured Markdown output
- **Metadata Extraction**: Title, author, publish date, and more
- **Image Extraction**: Optional image URL extraction
- **Pay-per-use**: Transparent pricing at $0.0015 per request

### Authentication

All API requests require a Bearer token:

```
Authorization: Bearer sk_live_your_api_key
```

### Quick Start

```bash
curl -X POST https://api.companyrm.lk/v1/extract \\
  -H "Authorization: Bearer sk_live_your_api_key" \\
  -H "Content-Type: application/json" \\
  -d '{"url": "https://example.com/article"}'
```
    """,
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "https://companyrm.lk",
        "https://www.companyrm.lk",
        "https://api.companyrm.lk"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add custom middleware (order matters: last added = first executed)
# RateLimiter runs after Auth (needs API key info), Auth runs after Logging
app.add_middleware(RateLimiterMiddleware)
app.add_middleware(AuthMiddleware)
app.add_middleware(LoggingMiddleware)

# Include API routers
app.include_router(v1_router)


# Health check endpoint
@app.get("/", tags=["health"])
async def root():
    """Root endpoint with API information."""
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "docs": "/docs",
        "health": "/health"
    }


@app.get("/health", tags=["health"])
async def health_check():
    """Health check endpoint for load balancers."""
    return {"status": "healthy"}


# Main entry point for development
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug
    )
