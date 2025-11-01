"""Portfolio repository for database operations."""
from datetime import date, datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database.models.portfolio import Portfolio as PortfolioModel
from app.database.models.portfolio import Position as PositionModel
from app.database.models.portfolio import Transaction as TransactionModel
from app.database.repositories.base import BaseRepository


class PortfolioRepository(BaseRepository[PortfolioModel, BaseModel, BaseModel]):
    """Repository for Portfolio model with custom methods."""

    def __init__(self):
        """Initialize with Portfolio model."""
        super().__init__(PortfolioModel)

    def get_by_name(self, db: Session, *, name: str) -> Optional[PortfolioModel]:
        """Get a portfolio by name."""
        return db.query(self.model).filter(self.model.name == name).first()

    def get_active_portfolios(self, db: Session) -> List[PortfolioModel]:
        """Get all active portfolios."""
        return db.query(self.model).filter(self.model.is_active == True).all()  # noqa: E712

    def get_portfolio_positions(
        self, db: Session, *, portfolio_id: int
    ) -> List[PositionModel]:
        """Get all positions for a portfolio."""
        portfolio = self.get(db, id=portfolio_id)
        return portfolio.positions if portfolio else []

    def get_portfolio_value_history(
        self, db: Session, *, portfolio_id: int, start_date: date, end_date: date
    ) -> List[Dict[str, Any]]:
        """Get historical portfolio values for a date range."""
        # This is a simplified implementation
        # In a real app, you'd want to use a time-series database or materialized view
        portfolio = self.get(db, id=portfolio_id)
        if not portfolio:
            return []

        # This is a placeholder - implement actual historical value calculation
        return [
            {
                "date": start_date,
                "value": float(portfolio.initial_cash or 0),
                "cash_balance": float(portfolio.initial_cash or 0),
                "invested_amount": 0.0,
            }
        ]


class PositionRepository(BaseRepository[PositionModel, BaseModel, BaseModel]):
    """Repository for Position model with custom methods."""

    def __init__(self):
        """Initialize with Position model."""
        super().__init__(PositionModel)

    def get_by_symbol(
        self, db: Session, *, portfolio_id: int, symbol: str
    ) -> Optional[PositionModel]:
        """Get a position by symbol within a portfolio."""
        return (
            db.query(self.model)
            .filter(
                self.model.portfolio_id == portfolio_id,
                self.model.symbol == symbol.upper(),
            )
            .first()
        )

    def get_portfolio_positions(
        self, db: Session, *, portfolio_id: int
    ) -> List[PositionModel]:
        """Get all positions for a portfolio."""
        return (
            db.query(self.model)
            .filter(self.model.portfolio_id == portfolio_id)
            .all()
        )

    def update_position_from_transaction(
        self, db: Session, *, transaction: TransactionModel
    ) -> PositionModel:
        """Update a position based on a transaction."""
        position = (
            db.query(self.model)
            .filter(
                self.model.portfolio_id == transaction.portfolio_id,
                self.model.symbol == transaction.symbol,
            )
            .first()
        )

        if not position:
            # Create new position if it doesn't exist
            position = self.model(
                portfolio_id=transaction.portfolio_id,
                symbol=transaction.symbol,
                quantity=Decimal("0"),
                cost_basis=Decimal("0"),
            )
            db.add(position)

        # Update position based on transaction type
        if transaction.transaction_type == "BUY":
            total_cost = (transaction.quantity * transaction.price) + transaction.commission
            new_quantity = position.quantity + transaction.quantity
            
            # Update average cost basis
            if new_quantity > 0:
                position.cost_basis = (
                    (position.cost_basis * position.quantity) + total_cost
                ) / new_quantity
            
            position.quantity = new_quantity
            
        elif transaction.transaction_type == "SELL":
            position.quantity -= transaction.quantity
            # For simplicity, we're not adjusting cost basis on partial sales
            # In a real app, you might want to implement FIFO/LIFO or other methods

        db.commit()
        db.refresh(position)
        return position


class TransactionRepository(BaseRepository[TransactionModel, BaseModel, BaseModel]):
    """Repository for Transaction model with custom methods."""

    def __init__(self):
        """Initialize with Transaction model."""
        super().__init__(TransactionModel)

    def get_portfolio_transactions(
        self, db: Session, *, portfolio_id: int, limit: int = 100
    ) -> List[TransactionModel]:
        """Get transactions for a portfolio, most recent first."""
        return (
            db.query(self.model)
            .filter(self.model.portfolio_id == portfolio_id)
            .order_by(self.model.date.desc(), self.model.id.desc())
            .limit(limit)
            .all()
        )

    def get_symbol_transactions(
        self, db: Session, *, portfolio_id: int, symbol: str, limit: int = 100
    ) -> List[TransactionModel]:
        """Get transactions for a specific symbol in a portfolio."""
        return (
            db.query(self.model)
            .filter(
                self.model.portfolio_id == portfolio_id,
                self.model.symbol == symbol.upper(),
            )
            .order_by(self.model.date.desc(), self.model.id.desc())
            .limit(limit)
            .all()
        )

    def get_transactions_in_date_range(
        self,
        db: Session,
        *,
        portfolio_id: int,
        start_date: date,
        end_date: date,
        symbol: Optional[str] = None,
    ) -> List[TransactionModel]:
        """Get transactions within a date range, optionally filtered by symbol."""
        query = db.query(self.model).filter(
            self.model.portfolio_id == portfolio_id,
            self.model.date >= start_date,
            self.model.date <= end_date,
        )

        if symbol:
            query = query.filter(self.model.symbol == symbol.upper())

        return query.order_by(self.model.date, self.model.id).all()
