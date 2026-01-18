"""
Extract Endpoint
POST /v1/extract - Extract clean Markdown from a URL.
"""
import uuid
from datetime import datetime
from typing import Union
from fastapi import APIRouter, Request, Depends, HTTPException
from sqlalchemy.orm import Session
import httpx

from app.db.database import get_db
from app.db.crud import increment_api_key_usage, create_usage_log
from app.schemas.extract import (
    ExtractRequest,
    ExtractSuccessResponse,
    ContentInfo,
    MetadataInfo,
    ImageInfo,
    UsageInfo,
)
from app.schemas.errors import ExtractErrorResponse, ErrorCodes, ERROR_STATUS_CODES
from app.services.extractor import ContentExtractor
from app.middleware.usage import UsageCalculator

router = APIRouter()
usage_calculator = UsageCalculator()


@router.post(
    "/extract",
    response_model=Union[ExtractSuccessResponse, ExtractErrorResponse],
    summary="Extract content from URL",
    description="""
    Extract clean, LLM-optimized Markdown content from any web URL.
    
    **Features:**
    - Removes ads, navigation, sidebars, and tracking scripts
    - Extracts main article content using Mozilla Readability
    - Converts to clean Markdown
    - Extracts metadata (title, author, date, etc.)
    - Optionally extracts image URLs
    
    **Pricing:**
    - Base: $0.0015 per successful request
    - Large pages (>500KB): +$0.001
    - Image extraction: +$0.002
    """,
    responses={
        200: {"description": "Successful extraction"},
        400: {"description": "Invalid request"},
        401: {"description": "Invalid API key"},
        429: {"description": "Rate limit exceeded"},
        502: {"description": "Failed to fetch URL"},
        504: {"description": "URL fetch timeout"},
    }
)
async def extract_content(
    request: Request,
    body: ExtractRequest,
    db: Session = Depends(get_db)
):
    """
    Extract clean Markdown content from a URL.
    
    This endpoint fetches the target URL, extracts the main content
    using the Readability algorithm, and converts it to clean Markdown.
    """
    request_id = getattr(request.state, 'request_id', f"req_{uuid.uuid4().hex[:12]}")
    api_key = getattr(request.state, 'api_key', None)
    
    try:
        # Initialize extractor with options
        extractor = ContentExtractor(
            timeout_ms=body.options.timeout_ms,
            markdown_flavor=body.options.markdown_flavor
        )
        
        # Perform extraction
        result = await extractor.extract(
            url=str(body.url),
            include_images=body.options.include_images,
            include_metadata=body.options.include_metadata,
            max_content_length=body.options.max_content_length
        )
        
        # Calculate billing
        billable_units, cost_usd = usage_calculator.calculate_cost(
            content_size_kb=result.content_size_kb,
            include_images=body.options.include_images,
            api_key=api_key
        )
        
        # Update API key usage
        if api_key:
            increment_api_key_usage(db, api_key)
        
        # Log usage
        if api_key:
            create_usage_log(
                db=db,
                request_id=request_id,
                api_key_id=api_key.id,
                url=str(body.url),
                billable_units=billable_units,
                cost_usd=cost_usd,
                content_size_kb=result.content_size_kb,
                output_size_kb=result.output_size_kb,
                processing_time_ms=result.processing_time_ms,
                success=True
            )
        
        # Build response
        response = ExtractSuccessResponse(
            success=True,
            request_id=request_id,
            url=str(body.url),
            extracted_at=datetime.utcnow(),
            content=ContentInfo(
                markdown=result.markdown,
                text_length=result.text_length,
                estimated_tokens=result.estimated_tokens
            ),
            metadata=MetadataInfo(
                title=result.metadata.title,
                author=result.metadata.author,
                published_date=result.metadata.published_date,
                site_name=result.metadata.site_name,
                excerpt=result.metadata.excerpt,
                lang=result.metadata.lang
            ) if body.options.include_metadata else None,
            images=[
                ImageInfo(url=img.url, alt=img.alt, position=img.position)
                for img in result.images
            ] if body.options.include_images else None,
            usage=UsageInfo(
                billable_units=billable_units,
                cost_usd=cost_usd
            )
        )
        
        return response
        
    except httpx.TimeoutException:
        return _error_response(
            db, request_id, api_key, str(body.url),
            ErrorCodes.FETCH_TIMEOUT,
            f"Target URL took >{body.options.timeout_ms}ms to respond"
        )
    
    except httpx.HTTPStatusError as e:
        return _error_response(
            db, request_id, api_key, str(body.url),
            ErrorCodes.FETCH_FAILED,
            f"Failed to fetch URL: HTTP {e.response.status_code}"
        )
    
    except httpx.RequestError as e:
        return _error_response(
            db, request_id, api_key, str(body.url),
            ErrorCodes.FETCH_FAILED,
            f"Failed to fetch URL: {str(e)}"
        )
    
    except Exception as e:
        return _error_response(
            db, request_id, api_key, str(body.url),
            ErrorCodes.EXTRACTION_FAILED,
            f"Extraction failed: {str(e)}"
        )


def _error_response(
    db: Session,
    request_id: str,
    api_key,
    url: str,
    error_code: str,
    message: str
) -> ExtractErrorResponse:
    """Create error response and log failed request."""
    billable = usage_calculator.is_billable_error(error_code)
    
    # Log failed request
    if api_key:
        create_usage_log(
            db=db,
            request_id=request_id,
            api_key_id=api_key.id,
            url=url,
            billable_units=1 if billable else 0,
            cost_usd=0.0,
            success=False,
            error_code=error_code
        )
    
    return ExtractErrorResponse(
        success=False,
        request_id=request_id,
        error={
            "code": error_code,
            "message": message,
            "billable": billable
        }
    )
