"""
Configuration Management
Loads environment variables and provides typed settings for the application.
"""
from functools import lru_cache
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Application
    app_name: str = "Clean Reader API"
    app_version: str = "1.0.0"
    debug: bool = False
    
    # Database
    database_url: str = "sqlite:///./cleanreader.db"
    
    # Security
    secret_key: str = "change-this-in-production"
    
    # Pricing (USD)
    base_price: float = 0.0015
    large_page_price: float = 0.001
    image_extraction_price: float = 0.002
    pdf_extraction_price: float = 0.003
    
    # Limits
    max_content_size_kb: int = 500
    max_output_size_kb: int = 50
    request_timeout_ms: int = 5000
    free_tier_requests: int = 100
    
    # Usage Alert Thresholds (percentage)
    alert_threshold_warning: int = 80
    alert_threshold_critical: int = 100

    @property
    def sync_database_url(self) -> str:
        """Fix for Postgres URL prefix used by Vercel/Heroku."""
        if self.database_url.startswith("postgres://"):
            return self.database_url.replace("postgres://", "postgresql://", 1)
        return self.database_url

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


# Tier Configuration - Centralized tier definitions
TIER_CONFIG = {
    "free": {
        "name": "Free",
        "monthly_limit": 100,
        "rate_limit_per_minute": 10,
        "rate_limit_per_day": 100,
        "price_monthly": 0.0,
        "discount": 1.0,  # No discount (100% of base price, but free tier doesn't charge)
        "features": ["Basic content extraction", "Markdown output"]
    },
    "developer": {
        "name": "Developer",
        "monthly_limit": 5000,
        "rate_limit_per_minute": 60,
        "rate_limit_per_day": 2000,
        "price_monthly": 7.50,
        "discount": 1.0,  # Standard pricing
        "features": ["All Free features", "Priority support", "Higher rate limits"]
    },
    "standard": {
        "name": "Standard",
        "monthly_limit": 1000,
        "rate_limit_per_minute": 30,
        "rate_limit_per_day": 500,
        "price_monthly": 0.0,
        "discount": 1.0,
        "features": ["Basic content extraction", "Pay-per-use billing"]
    },
    "pro": {
        "name": "Pro",
        "monthly_limit": 25000,
        "rate_limit_per_minute": 300,
        "rate_limit_per_day": 10000,
        "price_monthly": 30.00,
        "discount": 0.9,  # 10% discount
        "features": ["All Developer features", "Image extraction", "PDF support"]
    },
    "business": {
        "name": "Business",
        "monthly_limit": 100000,
        "rate_limit_per_minute": 1000,
        "rate_limit_per_day": 50000,
        "price_monthly": 100.00,
        "discount": 0.7,  # 30% discount
        "features": ["All Pro features", "Dedicated support", "SLA guarantee"]
    },
    "enterprise": {
        "name": "Enterprise",
        "monthly_limit": None,  # Unlimited
        "rate_limit_per_minute": 5000,
        "rate_limit_per_day": None,  # Unlimited
        "price_monthly": None,  # Custom pricing
        "discount": 0.6,  # 40% discount
        "features": ["All Business features", "Custom integrations", "On-premise option"]
    }
}


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
