"""Portfolio model."""
from datetime import date
from decimal import Decimal
from typing import List, Optional

from sqlalchemy import Boolean, Column, Date, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.orm import relationship

from app.database.models.base import Base


class Portfolio(Base):
    """Portfolio model representing a collection of investments."""

    __tablename__ = "portfolios"

    name = Column(String(100), nullable=False, index=True)
    description = Column(Text, nullable=True)
    initial_cash = Column(Numeric(12, 2), default=0, nullable=False)
    currency = Column(String(3), default="USD", nullable=False)
    start_date = Column(Date, default=date.today, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)

    # Relationships
    positions = relationship("Position", back_populates="portfolio", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        """String representation of the Portfolio model."""
        return f"<Portfolio(id={self.id}, name='{self.name}')>"

    @property
    def total_value(self) -> Decimal:
        """Calculate the total value of the portfolio."""
        return sum(
            position.market_value for position in self.positions
            if position.market_value is not None
        )

    @property
    def cash_balance(self) -> Decimal:
        """Calculate the current cash balance."""
        # This is a simplified version - in a real app, you'd track transactions
        return self.initial_cash - sum(
            position.cost_basis for position in self.positions
        )

    @property
    def performance(self) -> Decimal:
        """Calculate the performance of the portfolio as a percentage."""
        if not self.initial_cash:
            return Decimal(0)
        return ((self.total_value - self.initial_cash) / self.initial_cash) * 100


class Position(Base):
    """Position model representing a single investment position."""

    __tablename__ = "positions"

    portfolio_id = Column(Integer, ForeignKey("portfolios.id", ondelete="CASCADE"), nullable=False)
    symbol = Column(String(20), nullable=False, index=True)
    quantity = Column(Numeric(12, 6), default=0, nullable=False)
    cost_basis = Column(Numeric(12, 2), default=0, nullable=False)
    target_allocation = Column(Numeric(5, 2), nullable=True)
    notes = Column(Text, nullable=True)

    # Relationships
    portfolio = relationship("Portfolio", back_populates="positions")
    transactions = relationship("Transaction", back_populates="position", cascade="all, delete-orphan")
    market_data = relationship("MarketData", back_populates="position", uselist=False, cascade="all, delete-orphan")

    def __repr__(self) -> str:
        """String representation of the Position model."""
        return f"<Position(id={self.id}, symbol='{self.symbol}', quantity={self.quantity})>"

    @property
    def market_value(self) -> Optional[Decimal]:
        """Calculate the current market value of the position."""
        if not self.market_data or self.market_data.price is None:
            return None
        return Decimal(self.quantity) * self.market_data.price

    @property
    def unrealized_pnl(self) -> Optional[Decimal]:
        """Calculate the unrealized profit/loss."""
        if self.market_value is None:
            return None
        return self.market_value - self.cost_basis

    @property
    def unrealized_pnl_percent(self) -> Optional[float]:
        """Calculate the unrealized profit/loss as a percentage."""
        if not self.cost_basis or self.unrealized_pnl is None:
            return None
        return float((self.unrealized_pnl / self.cost_basis) * 100)


class Transaction(Base):
    """Transaction model representing a buy/sell transaction."""

    __tablename__ = "transactions"

    class TransactionType:
        BUY = "BUY"
        SELL = "SELL"
        DIVIDEND = "DIVIDEND"
        SPLIT = "SPLIT"

    position_id = Column(Integer, ForeignKey("positions.id", ondelete="CASCADE"), nullable=False)
    transaction_type = Column(String(10), nullable=False)
    date = Column(Date, default=date.today, nullable=False)
    quantity = Column(Numeric(12, 6), nullable=False)
    price = Column(Numeric(12, 4), nullable=False)
    commission = Column(Numeric(10, 2), default=0, nullable=False)
    notes = Column(Text, nullable=True)

    # Relationships
    position = relationship("Position", back_populates="transactions")

    def __repr__(self) -> str:
        """String representation of the Transaction model."""
        return f"<Transaction(id={self.id}, type='{self.transaction_type}', symbol='{self.position.symbol if self.position else None}')>"
