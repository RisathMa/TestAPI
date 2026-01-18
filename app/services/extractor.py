"""
Content Extraction Service
Core logic for fetching URLs and extracting clean Markdown content.
Uses Mozilla Readability algorithm for content extraction.
"""
import re
import time
from typing import Optional, Tuple, List
from dataclasses import dataclass
import httpx
from readability import Document
import html2text
from app.config import get_settings

settings = get_settings()


@dataclass
class ExtractedImage:
    """Extracted image data."""
    url: str
    alt: Optional[str] = None
    position: Optional[str] = None


@dataclass
class ExtractedMetadata:
    """Extracted page metadata."""
    title: Optional[str] = None
    author: Optional[str] = None
    published_date: Optional[str] = None
    site_name: Optional[str] = None
    excerpt: Optional[str] = None
    lang: Optional[str] = None


@dataclass
class ExtractionResult:
    """Complete extraction result."""
    markdown: str
    text_length: int
    estimated_tokens: int
    metadata: ExtractedMetadata
    images: List[ExtractedImage]
    content_size_kb: float
    output_size_kb: float
    processing_time_ms: int


class ContentExtractor:
    """
    Extracts clean, LLM-optimized content from web pages.
    
    Features:
    - HTTP fetching with timeout handling
    - Readability-based content extraction
    - HTML to Markdown conversion
    - Metadata extraction
    - Image URL extraction
    """
    
    # User agent to avoid blocks
    USER_AGENT = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36 CleanReaderBot/1.0"
    )
    
    def __init__(self, timeout_ms: int = 5000, markdown_flavor: str = "github"):
        """
        Initialize extractor.
        
        Args:
            timeout_ms: Request timeout in milliseconds
            markdown_flavor: Output format (github, commonmark, plain)
        """
        self.timeout_seconds = timeout_ms / 1000
        self.markdown_flavor = markdown_flavor
        self._setup_html2text()
    
    def _setup_html2text(self) -> None:
        """Configure HTML to Markdown converter."""
        self.h2t = html2text.HTML2Text()
        self.h2t.ignore_links = False
        self.h2t.ignore_images = False
        self.h2t.ignore_emphasis = False
        self.h2t.body_width = 0  # Don't wrap lines
        
        if self.markdown_flavor == "plain":
            self.h2t.ignore_links = True
            self.h2t.ignore_images = True
    
    async def fetch_url(self, url: str) -> Tuple[str, int]:
        """
        Fetch URL content.
        
        Args:
            url: URL to fetch
        
        Returns:
            Tuple of (html_content, content_size_bytes)
        
        Raises:
            httpx.TimeoutException: If request times out
            httpx.HTTPError: For other HTTP errors
        """
        async with httpx.AsyncClient(
            timeout=self.timeout_seconds,
            follow_redirects=True,
            headers={"User-Agent": self.USER_AGENT}
        ) as client:
            response = await client.get(url)
            response.raise_for_status()
            content = response.text
            return content, len(content.encode('utf-8'))
    
    def extract_content(self, html: str) -> str:
        """
        Extract main content using Readability algorithm.
        Strips ads, navigation, sidebars, and other noise.
        
        Args:
            html: Raw HTML content
        
        Returns:
            Cleaned HTML containing only main article content
        """
        doc = Document(html)
        return doc.summary()
    
    def extract_metadata(self, html: str) -> ExtractedMetadata:
        """
        Extract metadata from HTML.
        
        Looks for:
        - Open Graph tags
        - Meta tags
        - Schema.org markup
        - HTML semantics
        """
        doc = Document(html)
        
        # Basic metadata from Readability
        title = doc.title()
        excerpt = doc.short_title()
        
        # Extract additional metadata using regex patterns
        author = self._extract_meta(html, 'author')
        published_date = self._extract_meta(html, 'article:published_time')
        site_name = self._extract_meta(html, 'og:site_name')
        lang = self._extract_lang(html)
        
        return ExtractedMetadata(
            title=title,
            author=author,
            published_date=published_date,
            site_name=site_name,
            excerpt=excerpt[:200] if excerpt else None,
            lang=lang
        )
    
    def _extract_meta(self, html: str, name: str) -> Optional[str]:
        """Extract meta tag content by name or property."""
        patterns = [
            rf'<meta\s+(?:name|property)=["\']?{name}["\']?\s+content=["\']([^"\']+)["\']',
            rf'<meta\s+content=["\']([^"\']+)["\']\s+(?:name|property)=["\']?{name}["\']?',
        ]
        for pattern in patterns:
            match = re.search(pattern, html, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        return None
    
    def _extract_lang(self, html: str) -> Optional[str]:
        """Extract language from HTML lang attribute."""
        match = re.search(r'<html[^>]*\slang=["\']([^"\']+)["\']', html, re.IGNORECASE)
        return match.group(1) if match else None
    
    def convert_to_markdown(self, html: str, max_length: int = 50000) -> str:
        """
        Convert HTML to clean Markdown.
        
        Args:
            html: HTML content
            max_length: Maximum output length
        
        Returns:
            Clean Markdown string
        """
        markdown = self.h2t.handle(html)
        
        # Clean up excessive whitespace
        markdown = re.sub(r'\n{3,}', '\n\n', markdown)
        markdown = markdown.strip()
        
        # Truncate if needed
        if len(markdown) > max_length:
            markdown = markdown[:max_length] + "\n\n[Content truncated...]"
        
        return markdown
    
    def extract_images(self, html: str) -> List[ExtractedImage]:
        """
        Extract image URLs from HTML.
        
        Returns list of images with URLs, alt text, and position.
        """
        images = []
        pattern = r'<img[^>]+src=["\']([^"\']+)["\'][^>]*(?:alt=["\']([^"\']*)["\'])?'
        
        matches = re.findall(pattern, html, re.IGNORECASE)
        for i, (url, alt) in enumerate(matches):
            position = "top" if i == 0 else "middle" if i < len(matches) - 1 else "bottom"
            images.append(ExtractedImage(url=url, alt=alt or None, position=position))
        
        return images
    
    def estimate_tokens(self, text: str) -> int:
        """
        Estimate LLM token count.
        Rough approximation: ~4 characters per token for English.
        """
        return len(text) // 4
    
    async def extract(
        self,
        url: str,
        include_images: bool = False,
        include_metadata: bool = True,
        max_content_length: int = 50000
    ) -> ExtractionResult:
        """
        Full extraction pipeline.
        
        Args:
            url: URL to extract
            include_images: Whether to extract image URLs
            include_metadata: Whether to extract metadata
            max_content_length: Maximum output length
        
        Returns:
            ExtractionResult with all extracted data
        """
        start_time = time.time()
        
        # Fetch URL
        html, content_size = await self.fetch_url(url)
        
        # Extract main content
        clean_html = self.extract_content(html)
        
        # Convert to Markdown
        markdown = self.convert_to_markdown(clean_html, max_content_length)
        
        # Extract metadata if requested
        metadata = self.extract_metadata(html) if include_metadata else ExtractedMetadata()
        
        # Extract images if requested
        images = self.extract_images(clean_html) if include_images else []
        
        processing_time = int((time.time() - start_time) * 1000)
        
        return ExtractionResult(
            markdown=markdown,
            text_length=len(markdown),
            estimated_tokens=self.estimate_tokens(markdown),
            metadata=metadata,
            images=images,
            content_size_kb=content_size / 1024,
            output_size_kb=len(markdown.encode('utf-8')) / 1024,
            processing_time_ms=processing_time
        )
