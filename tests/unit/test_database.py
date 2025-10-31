"""
Unit tests for database.py - Database Layer Tests

Test Suite 1: Database Layer Tests
- Portfolio Management
- Position Management
- Market Data Management
- Price History
- Database Transactions & Error Handling
"""
import pytest
from datetime import datetime
from database import DatabaseManager, Portfolio, Position, MarketData


class TestPortfolioManagement:
    """Test Suite 1.1: Portfolio Management"""
    
    def test_create_portfolio_valid(self, test_db, sample_portfolio_data):
        """
        Test 1.1.1: Create portfolio with valid data
        
        Expected: Portfolio is created successfully with all attributes set correctly
        """
        portfolio = test_db.create_portfolio(**sample_portfolio_data)
        
        assert portfolio is not None
        assert portfolio.id is not None
        assert portfolio.name == sample_portfolio_data['name']
        assert portfolio.description == sample_portfolio_data['description']
        assert portfolio.is_default == sample_portfolio_data['is_default']
        assert portfolio.created_at is not None
        
        # Verify portfolio is in database
        retrieved = test_db.get_portfolio(portfolio.id)
        assert retrieved is not None
        assert retrieved.name == sample_portfolio_data['name']
    
    def test_create_portfolio_duplicate_name(self, test_db, sample_portfolio_data):
        """
        Test 1.1.2: Create portfolio with duplicate name (should fail)
        
        Expected: Second portfolio with same name should raise IntegrityError
        """
        # Create first portfolio
        test_db.create_portfolio(**sample_portfolio_data)
        
        # Try to create duplicate - should fail
        with pytest.raises(Exception):  # SQLAlchemy IntegrityError
            test_db.create_portfolio(**sample_portfolio_data)
    
    def test_create_portfolio_missing_name(self, test_db):
        """
        Test 1.1.3: Create portfolio with invalid data (missing name)
        
        Expected: Should raise an exception
        """
        with pytest.raises(Exception):
            test_db.create_portfolio(name=None, description="Test")
    
    def test_get_portfolio_by_id_existing(self, test_db, sample_portfolio_data):
        """
        Test 1.1.4: Get portfolio by ID (existing)
        
        Expected: Returns correct portfolio object
        """
        created = test_db.create_portfolio(**sample_portfolio_data)
        retrieved = test_db.get_portfolio(created.id)
        
        assert retrieved is not None
        assert retrieved.id == created.id
        assert retrieved.name == created.name
    
    def test_get_portfolio_by_id_nonexistent(self, test_db):
        """
        Test 1.1.5: Get portfolio by ID (non-existent)
        
        Expected: Returns None
        """
        result = test_db.get_portfolio(99999)
        assert result is None
    
    def test_get_all_portfolios(self, test_db):
        """
        Test 1.1.6: Get all portfolios
        
        Expected: Returns list of all portfolios
        """
        # Create multiple portfolios
        portfolio1 = test_db.create_portfolio(name="Portfolio 1", description="First")
        portfolio2 = test_db.create_portfolio(name="Portfolio 2", description="Second")
        
        all_portfolios = test_db.get_all_portfolios()
        
        assert len(all_portfolios) >= 2
        portfolio_names = [p.name for p in all_portfolios]
        assert "Portfolio 1" in portfolio_names
        assert "Portfolio 2" in portfolio_names
    
    def test_get_default_portfolio(self, test_db):
        """
        Test 1.1.7: Get default portfolio
        
        Expected: Returns the portfolio marked as default
        """
        # Create non-default portfolio
        test_db.create_portfolio(name="Regular Portfolio", is_default=False)
        
        # Create default portfolio
        default = test_db.create_portfolio(name="Default Portfolio", is_default=True)
        
        retrieved_default = test_db.get_default_portfolio()
        
        assert retrieved_default is not None
        assert retrieved_default.is_default is True
        assert retrieved_default.id == default.id
    
    def test_update_portfolio(self, test_db, sample_portfolio_data):
        """
        Test 1.1.8: Update portfolio (name, description, is_default)
        
        Expected: Portfolio attributes are updated correctly
        """
        portfolio = test_db.create_portfolio(**sample_portfolio_data)
        
        # Update all fields
        updated = test_db.update_portfolio(
            portfolio.id,
            name="Updated Name",
            description="Updated Description",
            is_default=False
        )
        
        assert updated is not None
        assert updated.name == "Updated Name"
        assert updated.description == "Updated Description"
        assert updated.is_default is False
        
        # Verify in database
        retrieved = test_db.get_portfolio(portfolio.id)
        assert retrieved.name == "Updated Name"
    
    def test_update_portfolio_set_default_unsets_previous(self, test_db):
        """
        Test 1.1.11: Set default portfolio (should unset previous default)
        
        Expected: When setting a new default, the old default is unset
        """
        # Create first default portfolio
        portfolio1 = test_db.create_portfolio(name="First Default", is_default=True)
        
        # Create second portfolio and set as default
        portfolio2 = test_db.create_portfolio(name="Second Portfolio", is_default=False)
        test_db.update_portfolio(portfolio2.id, is_default=True)
        
        # Verify first is no longer default
        test_db.session.refresh(portfolio1)
        assert portfolio1.is_default is False
        
        # Verify second is now default
        test_db.session.refresh(portfolio2)
        assert portfolio2.is_default is True
    
    def test_delete_portfolio_without_positions(self, test_db, sample_portfolio_data):
        """
        Test 1.1.10: Delete portfolio (without positions)
        
        Expected: Portfolio is deleted successfully
        """
        portfolio = test_db.create_portfolio(**sample_portfolio_data)
        portfolio_id = portfolio.id
        
        test_db.delete_portfolio(portfolio_id)
        
        # Verify deletion
        retrieved = test_db.get_portfolio(portfolio_id)
        assert retrieved is None
    
    def test_delete_portfolio_with_positions_cascades(self, test_db, portfolio_with_positions):
        """
        Test 1.1.9: Delete portfolio (with positions - should cascade)
        
        Expected: Portfolio and all related positions are deleted
        """
        portfolio, position = portfolio_with_positions
        portfolio_id = portfolio.id
        position_id = position.id
        
        test_db.delete_portfolio(portfolio_id)
        
        # Verify portfolio is deleted
        assert test_db.get_portfolio(portfolio_id) is None
        
        # Verify position is also deleted (cascade)
        assert test_db.get_position(position_id) is None


class TestPositionManagement:
    """Test Suite 1.2: Position Management"""
    
    def test_add_position_valid(self, test_db, sample_position_data):
        """
        Test 1.2.1: Add position with valid data
        
        Expected: Position is created successfully with all attributes
        """
        # First create a portfolio
        portfolio = test_db.create_portfolio(name="Test Portfolio")
        
        # Add position
        position = test_db.add_position(
            portfolio_id=portfolio.id,
            **sample_position_data
        )
        
        assert position is not None
        assert position.id is not None
        assert position.ticker == sample_position_data['ticker']
        assert position.entry_price == sample_position_data['entry_price']
        assert position.quantity == sample_position_data['quantity']
        assert position.portfolio_id == portfolio.id
    
    def test_get_position_by_id_existing(self, test_db, portfolio_with_positions):
        """
        Test 1.2.3: Get position by ID (existing)
        
        Expected: Returns correct position object
        """
        portfolio, position = portfolio_with_positions
        retrieved = test_db.get_position(position.id)
        
        assert retrieved is not None
        assert retrieved.id == position.id
        assert retrieved.ticker == position.ticker
    
    def test_get_position_by_id_nonexistent(self, test_db):
        """
        Test 1.2.4: Get position by ID (non-existent)
        
        Expected: Returns None
        """
        result = test_db.get_position(99999)
        assert result is None
    
    def test_get_all_positions(self, test_db, sample_position_data):
        """
        Test 1.2.5: Get all positions
        
        Expected: Returns list of all positions across all portfolios頻度
        """
        portfolio1 = test_db.create_portfolio(name="Portfolio 1")
        portfolio2 = test_db.create_portfolio(name="Portfolio 2")
        
        # Add positions to both portfolios
        test_db.add_position(portfolio_id=portfolio1.id, ticker="AAPL", 
                           entry_date=datetime.now(), entry_price=100, quantity=5)
        test_db.add_position(portfolio_id=portfolio2.id, ticker="GOOGL",
                           entry_date=datetime.now(), entry_price=200, quantity=3)
        
        all_positions = test_db.get_all_positions()
        
        assert len(all_positions) >= 2
        tickers = [p.ticker for p in all_positions]
        assert "AAPL" in tickers
        assert "GOOGL" in tickers
    
    def test_get_portfolio_positions(self, test_db):
        """
        Test 1.2.6: Get portfolio positions (specific portfolio)
        
        Expected: Returns only positions for the specified portfolio
        """
        portfolio1 = test_db.create_portfolio(name="Portfolio 1")
        portfolio2 = test_db.create_portfolio(name="Portfolio 2")
        
        # Add positions
        pos1 = test_db.add_position(portfolio_id=portfolio1.id, ticker="AAPL",
                                   entry_date=datetime.now(), entry_price=100, quantity=5)
        test_db.add_position(portfolio_id=portfolio2.id, ticker="GOOGL",
                           entry_date=datetime.now(), entry_price=200, quantity=3)
        
        # Get positions for portfolio1 only
        positions = test_db.get_portfolio_positions(portfolio1.id)
        
        assert len(positions) == 1
        assert positions[0].ticker == "AAPL"
        assert positions[0].id == pos1.id
    
    def test_update_position(self, test_db, portfolio_with_positions):
        """
        Test 1.2.7: Update position (entry_price, quantity, notes)
        
        Expected: Position attributes are updated correctly
        """
        portfolio, position = portfolio_with_positions
        
        updated = test_db.update_position(
            position.id,
            entry_price=160.00,
            quantity=15,
            notes="Updated notes"
        )
        
        assert updated is not None
        assert updated.entry_price == 160.00
        assert updated.quantity == 15
        assert updated.notes == "Updated notes"
        
        # Verify in database
        retrieved = test_db.get_position(position.id)
        assert retrieved.entry_price == 160.00
    
    def test_delete_position_deletes_market_data(self, test_db, portfolio_with_positions, sample_market_data):
        """
        Test 1.2.8: Delete position (should delete related market_data)
        
        Expected: Position and its market_data are deleted
        """
        portfolio, position = portfolio_with_positions
        
        # Add market data
        test_db.update_market_data(position.id, sample_market_data)
        
        position_id = position.id
        test_db.delete_position(position_id)
        
        # Verify position is deleted
        assert test_db.get_position(position_id) is None
        
        # Verify market_data is also deleted
        assert test_db.get_market_data(position_id) is None


class TestMarketDataManagement:
    """Test Suite 1.3: Market Data Management"""
    
    def test_update_market_data_new_position(self, test_db, portfolio_with_positions, sample_market_data):
        """
        Test 1.3.1: Update market data (new position - should create)
        
        Expected: Market data record is created for the position
        """
        portfolio, position = portfolio_with_positions
        
        result = test_db.update_market_data(position.id, sample_market_data)
        
        assert result is not None
        assert result.position_id == position.id
        assert result.current_price == sample_market_data['current_price']
        assert result.ticker == position.ticker
    
    def test_update_market_data_existing_position(self, test_db, portfolio_with_positions, sample_market_data):
        """
        Test 1.3.2: Update market data (existing position - should update)
        
        Expected: Existing market data record is updated
        """
        portfolio, position = portfolio_with_positions
        
        # Create initial market data
        test_db.update_market_data(position.id, sample_market_data)
        
        # Update with new values
        updated_data = sample_market_data.copy()
        updated_data['current_price'] = 165.00
        
        result = test_db.update_market_data(position.id, updated_data)
        
        assert result.current_price == 165.00
        assert result.position_id == position.id
    
    def test_update_market_data_json_serialization(self, test_db, portfolio_with_positions, sample_market_data):
        """
        Test 1.3.3: Update market data with quarterly_revenue/net_income (JSON serialization)
        
        Expected: Dict fields are properly serialized to JSON and can be retrieved
        """
        portfolio, position = portfolio_with_positions
        
        result = test_db.update_market_data(position.id, sample_market_data)
        
        # Verify JSON fields are stored as strings
        import json
        assert isinstance(result.quarterly_revenue, str) or result.quarterly_revenue is None
        assert isinstance(result.quarterly_net_income, str) or result.quarterly_net_income is None
        
        # Verify can be deserialized
        if result.quarterly_revenue:
            revenue_dict = json.loads(result.quarterly_revenue)
            assert isinstance(revenue_dict, dict)
            assert '2024-01-01' in revenue_dict


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

