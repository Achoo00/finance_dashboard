"""
Test suite for Market Data Management functionality.
"""
import pytest
import json
from datetime import datetime, timedelta
from sqlalchemy.exc import IntegrityError
from database import DatabaseManager, MarketData, Position

class TestMarketDataManagement:
    """Test cases for Market Data Management functionality."""
    
    @pytest.fixture(autouse=True)
    def setup_and_teardown(self, test_db):
        """Setup and teardown for each test."""
        self.db = test_db
        
        # Create a test portfolio
        self.portfolio = self.db.create_portfolio(
            name="Test Portfolio",
            description="Test Portfolio Description"
        )
        
        # Create a test position
        self.position = self.db.add_position(
            portfolio_id=self.portfolio.id,
            ticker="AAPL",
            entry_date=datetime(2023, 1, 1).date(),
            entry_price=150.0,
            quantity=10
        )
        
        # Sample market data
        self.test_market_data = {
            'current_price': 155.0,
            'daily_change': 2.5,
            'daily_change_percent': 1.64,
            'market_cap': 2500000000000,
            'pe_ratio': 28.5,
            'dividend_yield': 0.58,
            'volume': 50000000,
            'avg_volume': 45000000,
            'fifty_two_week_high': 198.23,
            'fifty_two_week_low': 124.17,
            'rsi': 65.3,
            'ma50': 148.7,
            'ma200': 142.3,
            'quarterly_revenue': {
                '2023-Q1': 117154000000,
                '2022-Q4': 90146000000,
                '2022-Q3': 82959000000,
                '2022-Q2': 97278000000
            },
            'net_income': {
                '2023-Q1': 29980000000,
                '2022-Q4': 20721000000,
                '2022-Q3': 19442000000,
                '2022-Q2': 25010000000
            },
            'last_updated': datetime.utcnow()
        }
        
        yield  # This is where the test runs
        
        # Cleanup (handled by test_db fixture)
    
    def test_update_market_data_new_position(self):
        """Test 1.3.1: Update market data for a new position (should create new market data)."""
        # Prepare market data
        market_data = {
            'current_price': 155.0,
            'day_low': 153.2,
            'day_high': 156.8,
            'fifty_two_week_low': 124.17,
            'fifty_two_week_high': 198.23,
            'volume': 50000000,
            'avg_volume': 45000000,
            'market_cap': 2500000000000,
            'pe_ratio': 28.5,
            'forward_pe': 25.7,
            'eps': 5.44,
            'profit_margin': 25.6,
            'dividend_yield': 0.58,
            'next_earnings_date': datetime(2023, 7, 27),
            'quarterly_revenue': {
                '2023-Q1': 117154000000,
                '2022-Q4': 90146000000,
                '2022-Q3': 82959000000,
                '2022-Q2': 97278000000
            },
            'quarterly_net_income': {
                '2023-Q1': 29980000000,
                '2022-Q4': 20721000000,
                '2022-Q3': 19442000000,
                '2022-Q2': 25010000000
            }
        }
        
        # Prepare technical data
        technical_data = {
            'rsi': 65.3,
            'macd': 2.5,
            'macd_signal': 2.2,
            'sma_50': 148.7,
            'sma_200': 142.3,
            'is_above_50_sma': True,
            'is_above_200_sma': True,
            'rsi_overbought': False,
            'rsi_oversold': False,
            'macd_crossover': True
        }
        
        # Act
        result = self.db.update_market_data(
            position_id=self.position.id,
            market_data=market_data,
            technical_data=technical_data
        )
        
        # Assert
        assert result is not None
        assert result.position_id == self.position.id
        assert result.ticker == self.position.ticker
        assert result.current_price == market_data['current_price']
        assert result.day_low == market_data['day_low']
        assert result.day_high == market_data['day_high']
        assert result.fifty_two_week_low == market_data['fifty_two_week_low']
        assert result.fifty_two_week_high == market_data['fifty_two_week_high']
        assert result.volume == market_data['volume']
        assert result.avg_volume == market_data['avg_volume']
        assert result.market_cap == market_data['market_cap']
        assert result.pe_ratio == market_data['pe_ratio']
        assert result.dividend_yield == market_data['dividend_yield']
        
        # Verify technical indicators
        assert result.rsi == technical_data['rsi']
        assert result.macd == technical_data['macd']
        assert result.sma_50 == technical_data['sma_50']
        assert result.sma_200 == technical_data['sma_200']
        
        # Verify JSON fields
        assert json.loads(result.quarterly_revenue) == market_data['quarterly_revenue']
        assert json.loads(result.quarterly_net_income) == market_data['quarterly_net_income']
        
        # Verify the market data is in the database
        db_market_data = self.db.get_market_data(self.position.id)
        assert db_market_data is not None
        assert db_market_data.position_id == self.position.id
    
    def test_update_market_data_existing_position(self):
        """Test 1.3.2: Update market data for an existing position (should update existing market data)."""
        # Arrange - create initial market data
        initial_market_data = {
            'current_price': 155.0,
            'volume': 50000000,
            'pe_ratio': 28.5,
            'quarterly_revenue': {
                '2023-Q1': 117154000000,
                '2022-Q4': 90146000000
            },
            'quarterly_net_income': {
                '2023-Q1': 29980000000,
                '2022-Q4': 20721000000
            }
        }
        
        initial_technical_data = {
            'rsi': 65.3,
            'macd': 2.5,
            'sma_50': 148.7,
            'sma_200': 142.3
        }
        
        # Create initial market data
        self.db.update_market_data(
            position_id=self.position.id,
            market_data=initial_market_data,
            technical_data=initial_technical_data
        )
        
        # Prepare updated market data
        updated_market_data = {
            'current_price': 160.0,
            'volume': 55000000,
            'pe_ratio': 29.1,
            'quarterly_revenue': {
                '2023-Q1': 120000000000,  # Updated
                '2022-Q4': 90146000000,
                '2022-Q3': 82959000000    # Added
            },
            'quarterly_net_income': {
                '2023-Q1': 31000000000,   # Updated
                '2022-Q4': 20721000000,
                '2022-Q3': 19442000000    # Added
            }
        }
        
        updated_technical_data = {
            'rsi': 68.5,  # Updated
            'macd': 3.2,  # Updated
            'sma_50': 150.2,  # Updated
            'sma_200': 143.1  # Updated
        }
        
        # Act - update the market data
        result = self.db.update_market_data(
            position_id=self.position.id,
            market_data=updated_market_data,
            technical_data=updated_technical_data
        )
        
        # Assert
        assert result is not None
        assert result.position_id == self.position.id
        assert result.current_price == updated_market_data['current_price']
        assert result.volume == updated_market_data['volume']
        assert result.pe_ratio == updated_market_data['pe_ratio']
        
        # Verify technical indicators were updated
        assert result.rsi == updated_technical_data['rsi']
        assert result.macd == updated_technical_data['macd']
        assert result.sma_50 == updated_technical_data['sma_50']
        assert result.sma_200 == updated_technical_data['sma_200']
        
        # Verify JSON fields were updated
        assert json.loads(result.quarterly_revenue) == updated_market_data['quarterly_revenue']
        assert json.loads(result.quarterly_net_income) == updated_market_data['quarterly_net_income']
    
    def test_update_market_data_with_financials(self):
        """Test 1.3.3: Update market data with quarterly_revenue and quarterly_net_income (JSON serialization)."""
        # Arrange
        financials_data = {
            'quarterly_revenue': {
                '2023-Q1': 120000000000,
                '2022-Q4': 90146000000,
                '2022-Q3': 82959000000,
                '2022-Q2': 97278000000
            },
            'quarterly_net_income': {
                '2023-Q1': 31000000000,
                '2022-Q4': 20721000000,
                '2022-Q3': 19442000000,
                '2022-Q2': 25010000000
            },
            'current_price': 155.0,
            'volume': 50000000
        }
        
        # Act
        market_data = self.db.update_market_data(
            position_id=self.position.id,
            market_data=financials_data
        )
        
        # Assert
        assert market_data is not None
        assert json.loads(market_data.quarterly_revenue) == financials_data['quarterly_revenue']
        assert json.loads(market_data.quarterly_net_income) == financials_data['quarterly_net_income']
        
        # Verify the data was properly serialized to JSON in the database
        db_market_data = self.db.get_market_data(self.position.id)
        assert json.loads(db_market_data.quarterly_revenue) == financials_data['quarterly_revenue']
        assert json.loads(db_market_data.quarterly_net_income) == financials_data['quarterly_net_income']
    
    def test_get_market_data_by_position_id_existing(self):
        """Test 1.3.4: Get market data by position_id (existing)."""
        # Arrange - create market data
        test_data = {
            'current_price': 155.0,
            'volume': 50000000,
            'pe_ratio': 28.5,
            'quarterly_revenue': {
                '2023-Q1': 117154000000,
                '2022-Q4': 90146000000
            }
        }
        
        self.db.update_market_data(
            position_id=self.position.id,
            market_data=test_data
        )
        
        # Act
        market_data = self.db.get_market_data(self.position.id)
        
        # Assert
        assert market_data is not None
        assert market_data.position_id == self.position.id
        assert market_data.current_price == test_data['current_price']
        assert market_data.volume == test_data['volume']
        assert json.loads(market_data.quarterly_revenue) == test_data['quarterly_revenue']
    
    def test_get_market_data_by_position_id_nonexistent(self):
        """Test 1.3.5: Get market data by position_id (non-existent)."""
        # Act
        market_data = self.db.get_market_data(9999)  # Non-existent position_id
        
        # Assert
        assert market_data is None
    
    def test_market_data_json_serialization(self):
        """Test 1.3.6: Market data JSON serialization/deserialization."""
        # Arrange - create market data with JSON fields
        test_data = {
            'current_price': 155.0,
            'volume': 50000000,
            'quarterly_revenue': {
                '2023-Q1': 120000000000,
                '2022-Q4': 90146000000
            },
            'quarterly_net_income': {
                '2023-Q1': 31000000000,
                '2022-Q4': 20721000000
            }
        }
        
        # Act - create market data with JSON fields
        self.db.update_market_data(
            position_id=self.position.id,
            market_data=test_data
        )
        
        # Retrieve the market data
        market_data = self.db.get_market_data(self.position.id)
        
        # Assert
        assert market_data is not None
        assert json.loads(market_data.quarterly_revenue) == test_data['quarterly_revenue']
        assert json.loads(market_data.quarterly_net_income) == test_data['quarterly_net_income']
        
        # Test that the JSON data was properly serialized in the database
        db_market_data = self.db.session.get(MarketData, market_data.id)
        assert isinstance(db_market_data.quarterly_revenue, str)
        assert isinstance(db_market_data.quarterly_net_income, str)
        assert json.loads(db_market_data.quarterly_revenue) == test_data['quarterly_revenue']
        assert json.loads(db_market_data.quarterly_net_income) == test_data['quarterly_net_income']
    
    def test_update_market_data_with_technical_indicators(self):
        """Test 1.3.7: Update market data with technical indicators."""
        # Arrange - create market data with technical indicators
        market_data = {
            'current_price': 155.0,
            'volume': 50000000
        }
        
        technical_data = {
            'rsi': 68.5,
            'macd': 2.7,
            'macd_signal': 2.0,
            'sma_50': 148.7,
            'sma_200': 142.3,
            'is_above_50_sma': True,
            'is_above_200_sma': True,
            'rsi_overbought': False,
            'rsi_oversold': False,
            'macd_crossover': True
        }
        
        # Act - update market data with technical indicators
        result = self.db.update_market_data(
            position_id=self.position.id,
            market_data=market_data,
            technical_data=technical_data
        )
        
        # Assert
        assert result is not None
        assert result.position_id == self.position.id
        
        # Verify technical indicators were set correctly
        assert result.rsi == technical_data['rsi']
        assert result.macd == technical_data['macd']
        assert result.macd_signal == technical_data['macd_signal']
        assert result.sma_50 == technical_data['sma_50']
        assert result.sma_200 == technical_data['sma_200']
        assert result.is_above_50_sma == technical_data['is_above_50_sma']
        assert result.is_above_200_sma == technical_data['is_above_200_sma']
        assert result.rsi_overbought == technical_data['rsi_overbought']
        assert result.rsi_oversold == technical_data['rsi_oversold']
        assert result.macd_crossover == technical_data['macd_crossover']
        
        # Verify the data is retrievable from the database
        db_market_data = self.db.get_market_data(self.position.id)
        assert db_market_data is not None
        assert db_market_data.rsi == technical_data['rsi']
        assert db_market_data.macd == technical_data['macd']
