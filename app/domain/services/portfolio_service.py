""
Portfolio domain services for business logic operations.
"""
from datetime import date, datetime
from decimal import Decimal, ROUND_HALF_UP
from typing import Dict, List, Optional, Tuple

from app.domain.entities.portfolio import (
    Money, 
    Portfolio, 
    Position, 
    Transaction, 
    TransactionType
)


class PortfolioService:
    """Service class for portfolio-related business logic."""
    
    @staticmethod
    def calculate_portfolio_performance(
        portfolio: Portfolio,
        start_date: date,
        end_date: date = None
    ) -> Dict:
        """
        Calculate performance metrics for the portfolio over a date range.
        
        Args:
            portfolio: The portfolio to analyze
            start_date: Start date for the analysis
            end_date: End date for the analysis (defaults to today)
            
        Returns:
            Dictionary containing performance metrics
        """
        if end_date is None:
            end_date = date.today()
            
        # Filter transactions within date range
        period_txns = [
            txn for txn in portfolio.transactions
            if start_date <= txn.date <= end_date
        ]
        
        # Calculate period return
        start_value = PortfolioService._calculate_portfolio_value_at_date(
            portfolio, start_date
        )
        end_value = PortfolioService._calculate_portfolio_value_at_date(
            portfolio, end_date
        )
        
        if start_value.amount == 0:
            period_return = Decimal('0')
        else:
            period_return = (
                (end_value.amount - start_value.amount) / start_value.amount
            ).quantize(Decimal('0.0001'), rounding=ROUND_HALF_UP)
        
        # Calculate annualized return if period > 1 year
        years = (end_date - start_date).days / 365.25
        if years > 1:
            annualized_return = (
                (1 + period_return) ** (1 / years) - 1
            ).quantize(Decimal('0.0001'), rounding=ROUND_HALF_UP)
        else:
            annualized_return = None
        
        # Calculate volatility (simplified)
        # In a real implementation, you would use daily returns
        volatility = Decimal('0.0')  # Placeholder
        
        # Calculate drawdown
        max_drawdown = PortfolioService._calculate_max_drawdown(portfolio, start_date, end_date)
        
        return {
            'start_date': start_date,
            'end_date': end_date,
            'start_value': start_value,
            'end_value': end_value,
            'period_return': period_return,
            'annualized_return': annualized_return,
            'volatility': volatility,
            'max_drawdown': max_drawdown,
            'transaction_count': len(period_txns),
        }
    
    @staticmethod
    def _calculate_portfolio_value_at_date(
        portfolio: Portfolio, 
        as_of_date: date
    ) -> Money:
        """Calculate portfolio value as of a specific date."""
        # In a real implementation, you would use historical price data
        # For now, we'll use the current value for simplicity
        return portfolio.current_value
    
    @staticmethod
    def _calculate_max_drawdown(
        portfolio: Portfolio,
        start_date: date,
        end_date: date
    ) -> Decimal:
        """Calculate maximum drawdown for the portfolio."""
        # In a real implementation, you would use daily values
        # This is a simplified version
        return Decimal('0.0')  # Placeholder
    
    @staticmethod
    def rebalance_portfolio(
        portfolio: Portfolio,
        target_allocations: Dict[str, float],
        rebalance_date: date = None
    ) -> List[Transaction]:
        """
        Generate transactions to rebalance the portfolio to target allocations.
        
        Args:
            portfolio: The portfolio to rebalance
            target_allocations: Dictionary of {symbol: target_percentage}
            rebalance_date: Date for the rebalance transactions
            
        Returns:
            List of transactions to execute the rebalance
        """
        if rebalance_date is None:
            rebalance_date = date.today()
            
        # Validate target allocations sum to ~100%
        total_allocation = sum(target_allocations.values())
        if not (99.9 <= total_allocation <= 100.1):
            raise ValueError("Target allocations must sum to 100%")
            
        current_value = portfolio.current_value.amount
        transactions = []
        
        # Calculate target values for each position
        target_values = {
            symbol: (current_value * Decimal(str(percent)) / 100)
            for symbol, percent in target_allocations.items()
        }
        
        # Calculate current values
        current_values = {
            symbol: pos.market_value.amount if pos.market_value else Decimal('0')
            for symbol, pos in portfolio.positions.items()
        }
        
        # Calculate differences and generate transactions
        for symbol, target in target_values.items():
            current = current_values.get(symbol, Decimal('0'))
            difference = target - current
            
            if difference > 0 and symbol in portfolio.positions:
                # Buy more of existing position
                position = portfolio.positions[symbol]
                if position.current_price:
                    quantity = difference / position.current_price.amount
                    transactions.append(Transaction(
                        type=TransactionType.BUY,
                        symbol=symbol,
                        date=rebalance_date,
                        quantity=quantity,
                        price=position.current_price,
                        notes="Portfolio rebalance"
                    ))
            elif difference < 0 and symbol in portfolio.positions:
                # Sell part of position
                position = portfolio.positions[symbol]
                if position.current_price:
                    quantity = abs(difference) / position.current_price.amount
                    transactions.append(Transaction(
                        type=TransactionType.SELL,
                        symbol=symbol,
                        date=rebalance_date,
                        quantity=quantity,
                        price=position.current_price,
                        notes="Portfolio rebalance"
                    ))
        
        return transactions
    
    @staticmethod
    def calculate_asset_allocation(portfolio: Portfolio) -> Dict[str, float]:
        """
        Calculate current asset allocation as percentages.
        
        Returns:
            Dictionary of {symbol: allocation_percentage}
        """
        total_value = portfolio.current_value.amount
        if total_value == 0:
            return {}
            
        allocations = {}
        for symbol, position in portfolio.positions.items():
            if position.market_value:
                allocations[symbol] = float(
                    (position.market_value.amount / total_value) * 100
                )
                
        # Add cash allocation
        cash_pct = float((portfolio.cash_balance.amount / total_value) * 100)
        if cash_pct > 0.01:  # Only include if significant
            allocations['CASH'] = cash_pct
            
        return allocations
