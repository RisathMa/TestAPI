"""
Database Models
SQLAlchemy ORM models for API keys and usage tracking.
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.db.database import Base


class APIKey(Base):
    """
    API Key model for authentication and tier management.
    
    Tiers:
    - free: 100 requests/month
    - standard: Pay-per-use at base rates
    - enterprise: Bulk discounts (30% off for >100K requests)
    """
    __tablename__ = "api_keys"

    id = Column(Integer, primary_key=True, index=True)
    key = Column(String(64), unique=True, index=True, nullable=False)
    name = Column(String(255), nullable=False)  # Friendly name for the key
    tier = Column(String(20), default="free")   # free, standard, enterprise
    is_active = Column(Boolean, default=True)
    
    # Usage limits
    monthly_limit = Column(Integer, nullable=True)  # None = unlimited
    requests_this_month = Column(Integer, default=0)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    last_used_at = Column(DateTime, nullable=True)
    
    # Relationships
    usage_logs = relationship("UsageLog", back_populates="api_key")


class UsageLog(Base):
    """
    Usage log for tracking individual requests and billing.
    Each successful extraction creates a usage record.
    """
    __tablename__ = "usage_logs"

    id = Column(Integer, primary_key=True, index=True)
    request_id = Column(String(36), unique=True, index=True, nullable=False)
    api_key_id = Column(Integer, ForeignKey("api_keys.id"), nullable=False)
    
    # Request details
    url = Column(Text, nullable=False)
    
    # Billing
    billable_units = Column(Integer, default=1)
    cost_usd = Column(Float, default=0.0)
    
    # Response metrics
    content_size_kb = Column(Float, nullable=True)
    output_size_kb = Column(Float, nullable=True)
    processing_time_ms = Column(Integer, nullable=True)
    
    # Status
    success = Column(Boolean, default=True)
    error_code = Column(String(50), nullable=True)
    
    # Timestamp
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    api_key = relationship("APIKey", back_populates="usage_logs")
