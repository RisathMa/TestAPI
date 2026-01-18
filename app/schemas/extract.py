"""
Pydantic Schemas for Extract Endpoint
Request and response models with full validation.
"""
from datetime import datetime
from typing import Optional, List, Literal
from pydantic import BaseModel, Field, HttpUrl


# ============================================================================
# Request Schemas
# ============================================================================

class ExtractOptions(BaseModel):
    """Options for content extraction."""
    include_images: bool = Field(
        default=False,
        description="Extract image URLs from the content"
    )
    include_metadata: bool = Field(
        default=True,
        description="Include metadata like author, publish date"
    )
    markdown_flavor: Literal["github", "commonmark", "plain"] = Field(
        default="github",
        description="Markdown output format"
    )
    max_content_length: int = Field(
        default=50000,
        ge=1000,
        le=500000,
        description="Maximum character limit for output"
    )
    timeout_ms: int = Field(
        default=5000,
        ge=1000,
        le=30000,
        description="Maximum fetch time in milliseconds"
    )


class ExtractRequest(BaseModel):
    """Request body for /v1/extract endpoint."""
    url: HttpUrl = Field(
        ...,
        description="URL to extract content from"
    )
    options: ExtractOptions = Field(
        default_factory=ExtractOptions,
        description="Extraction options"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "url": "https://example.com/article",
                "options": {
                    "include_images": False,
                    "include_metadata": True,
                    "markdown_flavor": "github",
                    "max_content_length": 50000,
                    "timeout_ms": 5000
                }
            }
        }


# ============================================================================
# Response Schemas
# ============================================================================

class ContentInfo(BaseModel):
    """Extracted content information."""
    markdown: str = Field(description="Clean markdown content")
    text_length: int = Field(description="Character count of content")
    estimated_tokens: int = Field(description="Estimated LLM token count")


class MetadataInfo(BaseModel):
    """Extracted metadata."""
    title: Optional[str] = Field(None, description="Article title")
    author: Optional[str] = Field(None, description="Author name")
    published_date: Optional[str] = Field(None, description="Publication date")
    site_name: Optional[str] = Field(None, description="Website name")
    excerpt: Optional[str] = Field(None, description="Brief summary")
    lang: Optional[str] = Field(None, description="Content language")


class ImageInfo(BaseModel):
    """Extracted image information."""
    url: str = Field(description="Image URL")
    alt: Optional[str] = Field(None, description="Alt text")
    position: Optional[str] = Field(None, description="Position in content")


class UsageInfo(BaseModel):
    """Billing and usage information."""
    billable_units: int = Field(description="Number of billable units")
    cost_usd: float = Field(description="Cost in USD")


class ExtractSuccessResponse(BaseModel):
    """Successful extraction response."""
    success: Literal[True] = True
    request_id: str = Field(description="Unique request identifier")
    url: str = Field(description="Extracted URL")
    extracted_at: datetime = Field(description="Extraction timestamp")
    content: ContentInfo
    metadata: Optional[MetadataInfo] = None
    images: Optional[List[ImageInfo]] = None
    usage: UsageInfo

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "request_id": "req_xyz789",
                "url": "https://example.com/article",
                "extracted_at": "2026-01-19T14:23:45Z",
                "content": {
                    "markdown": "# Article Title\n\nClean content here...",
                    "text_length": 12450,
                    "estimated_tokens": 3200
                },
                "metadata": {
                    "title": "Article Title",
                    "author": "Jane Doe",
                    "published_date": "2026-01-15",
                    "site_name": "Example News",
                    "excerpt": "Brief summary...",
                    "lang": "en"
                },
                "images": [
                    {
                        "url": "https://example.com/hero.jpg",
                        "alt": "Hero image description",
                        "position": "top"
                    }
                ],
                "usage": {
                    "billable_units": 1,
                    "cost_usd": 0.0015
                }
            }
        }
