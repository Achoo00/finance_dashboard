""
Portfolio domain model and related value objects.
"""
from datetime import date
from decimal import Decimal
from enum import Enum
from typing import Dict, List, Optional

from pydantic import BaseModel, Field, validator


class Currency(str, Enum):
    """Supported currencies for portfolios."""
    USD = "USD"
    EUR = "EUR"
    GBP = "GBP"
    JPY = "JPY"


class TransactionType(str, Enum):
    """Types of financial transactions."""
    BUY = "BUY"
    SELL = "SELL"
    DIVIDEND = "DIVIDEND"
    DEPOSIT = "DEPOSIT"
    WITHDRAWAL = "WITHDRAWAL"


class Money(BaseModel):
    """Value object representing monetary amounts."""
    amount: Decimal = Field(..., gt=0, decimal_places=2)
    currency: Currency = Field(default=Currency.USD)

    def __add__(self, other: 'Money') -> 'Money':
        if self.currency != other.currency:
            raise ValueError("Cannot add money in different currencies")
        return Money(amount=self.amount + other.amount, currency=self.currency)

    def __sub__(self, other: 'Money') -> 'Money':
        if self.currency != other.currency:
            raise ValueError("Cannot subtract money in different currencies")
        return Money(amount=self.amount - other.amount, currency=self.currency)

    def __mul__(self, scalar: float) -> 'Money':
        return Money(amount=self.amount * Decimal(str(scalar)), currency=self.currency)


class Position(BaseModel):
    """Domain model for an investment position."""
    symbol: str = Field(..., min_length=1, max_length=20)
    quantity: Decimal = Field(..., gt=0, decimal_places=6)
    cost_basis: Money
    current_price: Optional[Money] = None
    target_allocation: Optional[Decimal] = Field(None, ge=0, le=100, decimal_places=2)
    notes: Optional[str] = None

    @validator('symbol')
    def symbol_uppercase(cls, v: str) -> str:
        return v.upper()

    @property
    def market_value(self) -> Optional[Money]:
        """Calculate the current market value of the position."""
        if self.current_price and self.quantity:
            return Money(
                amount=self.current_price.amount * self.quantity,
                currency=self.current_price.currency
            )
        return None

    @property
    def unrealized_pnl(self) -> Optional[Money]:
        """Calculate unrealized profit/loss."""
        if self.market_value and self.cost_basis:
            return Money(
                amount=self.market_value.amount - self.cost_basis.amount,
                currency=self.cost_basis.currency
            )
        return None

    @property
    def unrealized_pnl_percent(self) -> Optional[Decimal]:
        """Calculate unrealized P&L as a percentage."""
        if self.unrealized_pnl and self.cost_basis.amount > 0:
            return (self.unrealized_pnl.amount / self.cost_basis.amount) * 100
        return None


class Transaction(BaseModel):
    """Domain model for financial transactions."""
    type: TransactionType
    symbol: str
    date: date
    quantity: Decimal = Field(..., gt=0, decimal_places=6)
    price: Money
    commission: Money = Field(
        default_factory=lambda: Money(amount=Decimal('0'), currency=Currency.USD)
    )
    notes: Optional[str] = None

    @validator('symbol')
    def symbol_uppercase(cls, v: str) -> str:
        return v.upper()

    @property
    def total_amount(self) -> Money:
        """Calculate the total transaction amount."""
        if self.type in (TransactionType.BUY, TransactionType.DEPOSIT):
            return Money(
                amount=(self.price.amount * self.quantity) + self.commission.amount,
                currency=self.price.currency
            )
        else:  # SELL, WITHDRAWAL, DIVIDEND
            return Money(
                amount=(self.price.amount * self.quantity) - self.commission.amount,
                currency=self.price.currency
            )


class Portfolio(BaseModel):
    """Domain model for an investment portfolio."""
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    currency: Currency = Field(default=Currency.USD)
    initial_cash: Money = Field(
        default_factory=lambda: Money(amount=Decimal('0'), currency=Currency.USD)
    )
    start_date: date = Field(default_factory=date.today)
    is_active: bool = True
    positions: Dict[str, Position] = Field(default_factory=dict)
    transactions: List[Transaction] = Field(default_factory=list)

    @property
    def current_value(self) -> Money:
        """Calculate the current total value of the portfolio."""
        total = self.cash_balance.amount
        for position in self.positions.values():
            if position.market_value:
                total += position.market_value.amount
        return Money(amount=total, currency=self.currency)

    @property
    def cash_balance(self) -> Money:
        """Calculate the current cash balance."""
        # Start with initial cash
        cash = self.initial_cash.amount
        
        # Adjust based on transactions
        for txn in self.transactions:
            if txn.type == TransactionType.BUY:
                cash -= txn.total_amount.amount
            elif txn.type == TransactionType.SELL:
                cash += txn.total_amount.amount
            elif txn.type == TransactionType.DEPOSIT:
                cash += txn.total_amount.amount
            elif txn.type == TransactionType.WITHDRAWAL:
                cash -= txn.total_amount.amount
            # DIVIDEND increases cash
            elif txn.type == TransactionType.DIVIDEND:
                cash += txn.total_amount.amount
                
        return Money(amount=cash, currency=self.currency)

    def add_transaction(self, transaction: Transaction) -> None:
        """Add a transaction and update the portfolio state."""
        self.transactions.append(transaction)
        self._update_positions(transaction)

    def _update_positions(self, transaction: Transaction) -> None:
        """Update positions based on a transaction."""
        symbol = transaction.symbol
        position = self.positions.get(symbol)

        if transaction.type == TransactionType.BUY:
            if position is None:
                # Create new position
                position = Position(
                    symbol=symbol,
                    quantity=transaction.quantity,
                    cost_basis=transaction.total_amount,
                    current_price=transaction.price
                )
                self.positions[symbol] = position
            else:
                # Update existing position
                total_cost = (position.cost_basis.amount * position.quantity) + transaction.total_amount.amount
                new_quantity = position.quantity + transaction.quantity
                
                position.quantity = new_quantity
                position.cost_basis = Money(
                    amount=total_cost / new_quantity,
                    currency=position.cost_basis.currency
                )
                
        elif transaction.type == TransactionType.SELL:
            if position is None or position.quantity < transaction.quantity:
                raise ValueError("Insufficient position to sell")
                
            position.quantity -= transaction.quantity
            if position.quantity == 0:
                del self.positions[symbol]
