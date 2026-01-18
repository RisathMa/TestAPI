"""
Usage Tracking Service
Calculates billing and records usage for each request.
"""
from app.config import get_settings
from app.db.models import APIKey

settings = get_settings()


class UsageCalculator:
    """
    Calculates billing based on request characteristics.
    
    Pricing Model:
    - Base: $0.0015 per successful request
    - Large pages (>500KB): +$0.001
    - Image extraction: +$0.002
    - PDF extraction: +$0.003
    
    Discounts:
    - Enterprise tier (>100K requests/month): 30% off
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
        api_key: APIKey = None
    ) -> tuple[int, float]:
        """
        Calculate billing units and cost.
        
        Args:
            content_size_kb: Size of fetched content in KB
            include_images: Whether image extraction was requested
            is_pdf: Whether PDF extraction was requested
            api_key: API key for tier-based pricing
        
        Returns:
            Tuple of (billable_units, cost_usd)
        """
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
        
        # Enterprise discount
        if api_key and api_key.tier == "enterprise":
            cost *= 0.7  # 30% discount
        
        # Free tier: no charge (but still track units)
        if api_key and api_key.tier == "free":
            cost = 0.0
        
        return billable_units, round(cost, 6)
    
    def is_billable_error(self, error_code: str) -> bool:
        """
        Determine if an error should be billed.
        
        Non-billable errors:
        - Authentication failures
        - Rate limiting
        - Our server errors
        
        Billable errors:
        - Target site issues (we still did the work)
        """
        non_billable = {
            "INVALID_API_KEY",
            "API_KEY_DISABLED", 
            "RATE_LIMIT_EXCEEDED",
            "INTERNAL_ERROR",
            "INVALID_URL",
        }
        return error_code not in non_billable
