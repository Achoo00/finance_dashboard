"""Market data models."""
from datetime import date, datetime
from decimal import Decimal
from typing import Dict, Optional

from sqlalchemy import (
    Column,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    JSON,
)
from sqlalchemy.orm import relationship

from app.database.models.base import Base


class MarketData(Base):
    """Market data for a specific security."""

    __tablename__ = "market_data"

    symbol = Column(String(20), index=True, nullable=False)
    date = Column(Date, default=date.today, nullable=False, index=True)
    open_price = Column(Numeric(12, 4), nullable=True)
    high_price = Column(Numeric(12, 4), nullable=True)
    low_price = Column(Numeric(12, 4), nullable=True)
    close_price = Column(Numeric(12, 4), nullable=True)
    adj_close = Column(Numeric(12, 4), nullable=True)
    volume = Column(Numeric(20, 4), nullable=True)
    
    # Additional market data fields
    market_cap = Column(Numeric(20, 2), nullable=True)
    pe_ratio = Column(Numeric(10, 2), nullable=True)
    dividend_yield = Column(Numeric(10, 4), nullable=True)
    
    # Metadata
    source = Column(String(50), default="yfinance", nullable=False)
    last_updated = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Raw JSON data for flexibility
    raw_data = Column(JSON, nullable=True)

    # Relationships
    position = relationship("Position", back_populates="market_data")

    def __repr__(self) -> str:
        """String representation of the MarketData model."""
        return f"<MarketData(id={self.id}, symbol='{self.symbol}', date={self.date})>"

    @property
    def price(self) -> Optional[Decimal]:
        """Get the current price (using close price as default)."""
        return self.close_price


class StockNews(Base):
    """Stock news and announcements."""

    __tablename__ = "stock_news"

    symbol = Column(String(20), index=True, nullable=False)
    title = Column(String(255), nullable=False)
    summary = Column(Text, nullable=True)
    content = Column(Text, nullable=True)
    url = Column(String(512), nullable=True)
    source = Column(String(100), nullable=True)
    published_at = Column(DateTime, nullable=False, index=True)
    sentiment_score = Column(Numeric(5, 4), nullable=True)
    
    # Raw data
    raw_data = Column(JSON, nullable=True)

    def __repr__(self) -> str:
        """String representation of the StockNews model."""
        return f"<StockNews(id={self.id}, symbol='{self.symbol}', title='{self.title[:50]}...')>"


class EconomicIndicator(Base):
    """Economic indicators and market indices."""

    __tablename__ = "economic_indicators"

    name = Column(String(100), nullable=False, index=True)
    symbol = Column(String(20), index=True, nullable=False)
    value = Column(Numeric(20, 4), nullable=True)
    date = Column(Date, nullable=False, index=True)
    frequency = Column(String(20), default="daily", nullable=False)  # daily, weekly, monthly, quarterly, yearly
    unit = Column(String(20), nullable=True)  # e.g., %, $, index points
    
    # Metadata
    source = Column(String(50), nullable=False)
    last_updated = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Raw data
    raw_data = Column(JSON, nullable=True)

    def __repr__(self) -> str:
        """String representation of the EconomicIndicator model."""
        return f"<EconomicIndicator(id={self.id}, name='{self.name}', date={self.date})>"
