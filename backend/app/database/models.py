"""
Database models for caching and shareable links
"""

from sqlalchemy import Column, String, DateTime, Text, Integer, Boolean
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
import uuid

Base = declarative_base()


class GradingCache(Base):
    """
    Cache for portfolio grading results
    Saves API costs by storing results for 7 days
    """
    __tablename__ = "grading_cache"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    portfolio_url = Column(String(500), unique=True, nullable=False, index=True)
    result_data = Column(Text, nullable=False)  # JSON string
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    accessed_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    access_count = Column(Integer, default=0)

    def __repr__(self):
        return f"<GradingCache(url='{self.portfolio_url[:50]}...', created={self.created_at})>"


class ShareableLink(Base):
    """
    Shareable result links for portfolios
    Allows users to share their grading results
    """
    __tablename__ = "shareable_links"

    share_id = Column(String(12), primary_key=True)  # Short ID like 'abc123xyz'
    portfolio_url = Column(String(500), nullable=False)
    result_data = Column(Text, nullable=False)  # JSON string
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    expires_at = Column(DateTime, nullable=True)  # Optional expiration
    view_count = Column(Integer, default=0)
    is_public = Column(Boolean, default=True)

    def __repr__(self):
        return f"<ShareableLink(id='{self.share_id}', views={self.view_count})>"


class AnalyticsEvent(Base):
    """
    Simple analytics for understanding usage patterns
    Helps optimize the system and understand common issues
    """
    __tablename__ = "analytics_events"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    event_type = Column(String(50), nullable=False, index=True)  # 'analysis_started', 'analysis_completed', etc.
    portfolio_url = Column(String(500), nullable=True)
    event_data = Column(Text, nullable=True)  # JSON string with event details
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    ip_address = Column(String(45), nullable=True)  # IPv6 compatible

    def __repr__(self):
        return f"<AnalyticsEvent(type='{self.event_type}', time={self.timestamp})>"
