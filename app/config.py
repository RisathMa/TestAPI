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

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
