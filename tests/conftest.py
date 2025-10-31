"""
Pytest configuration and shared fixtures for all tests
"""
import pytest
import os
import tempfile
from database import DatabaseManager, Base, Portfolio, Position, MarketData
from sqlalchemy import create_engine
from datetime import datetime, timedelta
import sys

# Add parent directory to path to import modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


@pytest.fixture(scope="function")
def test_db():
    """
    Create an in-memory SQLite database for testing.
    Each test gets a fresh database instance.
    """
    # Use in-memory database for fast tests
    db_path = "sqlite:///:memory:"
    db = DatabaseManager(db_path=db_path)
    
    # Create all tables
    Base.metadata.create_all(db.engine)
    
    yield db
    
    # Cleanup
    db.session.close()
    db.close()


@pytest.fixture
def sample_portfolio_data():
    """Sample portfolio data for testing"""
    return {
        'name': 'Test Portfolio',
        'description': 'A test portfolio',
        'is_default': True
    }


@pytest.fixture
def sample_position_data():
    """Sample position data for testing"""
    return {
        'ticker': 'AAPL',
        'entry_date': datetime(2024, 1, 1),
        'entry_price': 150.00,
        'quantity': 10,
        'notes': 'Test position'
    }


@pytest.fixture
def sample_market_data():
    """Sample market data for testing"""
    return {
        'current_price': 155.00,
        'day_low': 154.00,
        'day_high': 156.00,
        'fifty_two_week_low': 140.00,
        'fifty_two_week_high': 180.00,
        'volume': 1000000,
        'avg_volume': 2000000,
        'market_cap': 2500000000000.0,
        'pe_ratio': 25.5,
        'forward_pe': 24.0,
        'eps': 6.10,
        'profit_margin': 0.25,
        'dividend_yield': 0.015,
        'next_earnings_date': datetime(2024, 2, 1),
        'quarterly_revenue': {
            '2024-01-01': 1000000000.0,
            '2023-10-01': 950000000.0,
            '2023-07-01': 900000000.0,
            '2023-04-01': 850000000.0
        },
        'quarterly_net_income': {
            '2024-01-01': 250000000.0,
            '2023-10-01': 237500000.0,
            '2023-07-01': 225000000.0,
            '2023-04-01': 212500000.0
        }
    }


@pytest.fixture
def portfolio_with_positions(test_db, sample_portfolio_data, sample_position_data):
    """Create a portfolio with one position for testing"""
    # Create portfolio
    portfolio = test_db.create_portfolio(**sample_portfolio_data)
    
    # Create position
    position = test_db.add_position(
        portfolio_id=portfolio.id,
        **sample_position_data
    )
    
    return portfolio, position

