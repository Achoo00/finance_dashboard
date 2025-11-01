"""
Unit tests for position management functionality in database.py

Test Suite 1.2: Position Management
"""
import pytest
from datetime import datetime, timedelta
from sqlalchemy.exc import IntegrityError
from database import DatabaseManager, Position, MarketData

class TestPositionManagement:
    """Test Suite 1.2: Position Management"""
    
    @pytest.fixture(autouse=True)
    def setup(self, test_db):
        """Setup test data before each test."""
        self.db = test_db
        # Create a test portfolio
        self.portfolio = self.db.create_portfolio(
            name="Test Portfolio",
            description="Test portfolio for position tests",
            is_default=True
        )
        self.test_ticker = "AAPL"
        self.test_entry_date = datetime.now() - timedelta(days=30)
        self.test_entry_price = 150.0
        self.test_quantity = 10
        self.test_notes = "Test position"
        
    def cleanup_test_data(self):
        """Clean up test data from the database."""
        # Delete all positions (this will cascade to market data)
        for position in self.db.get_all_positions():
            self.db.delete_position(position.id)
        
        # Delete all portfolios
        for portfolio in self.db.get_all_portfolios():
            self.db.delete_portfolio(portfolio.id)
    
    def test_add_position_valid(self):
        """Test 1.2.1: Add position with valid data"""
        # Act
        position = self.db.add_position(
            portfolio_id=self.portfolio.id,
            ticker=self.test_ticker,
            entry_date=self.test_entry_date,
            entry_price=self.test_entry_price,
            quantity=self.test_quantity,
            notes=self.test_notes
        )
        
        # Assert
        assert position is not None
        assert position.id is not None
        assert position.portfolio_id == self.portfolio.id
        assert position.ticker == self.test_ticker
        assert position.entry_date == self.test_entry_date
        assert position.entry_price == self.test_entry_price
        assert position.quantity == self.test_quantity
        assert position.notes == self.test_notes
        
        # Verify position is in database
        retrieved = self.db.get_position(position.id)
        assert retrieved is not None
        assert retrieved.ticker == self.test_ticker
    
    def test_add_position_invalid_portfolio_id(self):
        """Test 1.2.2: Add position with invalid portfolio_id (should fail or handle gracefully)"""
        # SQLite doesn't enforce foreign key constraints by default
        # So we'll test that the position can be created but the relationship won't work properly
        
        # Try to add a position with a non-existent portfolio
        try:
            position = self.db.add_position(
                portfolio_id=9999,  # Non-existent portfolio
                ticker=self.test_ticker,
                entry_date=self.test_entry_date,
                entry_price=self.test_entry_price,
                quantity=self.test_quantity
            )
            
            # If we get here, the database allowed the operation
            # This is the case for SQLite with foreign keys disabled
            
            # Verify the position exists in the database
            retrieved = self.db.get_position(position.id)
            assert retrieved is not None
            
            # The relationship to the non-existent portfolio should be broken
            # This is the best we can test in SQLite with foreign keys disabled
            
        except IntegrityError:
            # This is the expected behavior for databases with foreign key enforcement
            # or SQLite with foreign keys enabled
            pass
    
    def test_get_position_by_id_existing(self):
        """Test 1.2.3: Get position by ID (existing)"""
        # Arrange
        position = self.db.add_position(
            portfolio_id=self.portfolio.id,
            ticker=self.test_ticker,
            entry_date=self.test_entry_date,
            entry_price=self.test_entry_price,
            quantity=self.test_quantity
        )
        
        # Act
        retrieved = self.db.get_position(position.id)
        
        # Assert
        assert retrieved is not None
        assert retrieved.id == position.id
        assert retrieved.ticker == self.test_ticker
    
    def test_get_position_by_id_nonexistent(self):
        """Test 1.2.4: Get position by ID (non-existent)"""
        # Act
        position = self.db.get_position(99999)  # Non-existent ID
        
        # Assert
        assert position is None
    
    def test_get_all_positions(self):
        """Test 1.2.5: Get all positions"""
        # Arrange
        # Add multiple positions to different portfolios
        portfolio2 = self.db.create_portfolio(name="Portfolio 2")
        
        position1 = self.db.add_position(
            portfolio_id=self.portfolio.id,
            ticker="AAPL",
            entry_date=datetime.now() - timedelta(days=30),
            entry_price=150.0,
            quantity=10
        )
        
        position2 = self.db.add_position(
            portfolio_id=portfolio2.id,
            ticker="MSFT",
            entry_date=datetime.now() - timedelta(days=60),
            entry_price=300.0,
            quantity=5
        )
        
        # Act
        all_positions = self.db.get_all_positions()
        
        # Assert
        assert len(all_positions) == 2
        tickers = {p.ticker for p in all_positions}
        assert "AAPL" in tickers
        assert "MSFT" in tickers
    
    def test_get_portfolio_positions(self):
        """Test 1.2.6: Get portfolio positions (specific portfolio)"""
        # Arrange
        # Create a second portfolio
        portfolio2 = self.db.create_portfolio(name="Portfolio 2")
        
        # Add positions to both portfolios
        position1 = self.db.add_position(
            portfolio_id=self.portfolio.id,
            ticker="AAPL",
            entry_date=datetime.now() - timedelta(days=30),
            entry_price=150.0,
            quantity=10
        )
        
        position2 = self.db.add_position(
            portfolio_id=portfolio2.id,  # Different portfolio
            ticker="MSFT",
            entry_date=datetime.now() - timedelta(days=60),
            entry_price=300.0,
            quantity=5
        )
        
        # Act
        portfolio1_positions = self.db.get_portfolio_positions(self.portfolio.id)
        
        # Assert
        assert len(portfolio1_positions) == 1
        assert portfolio1_positions[0].ticker == "AAPL"
    
    def test_update_position(self):
        """Test 1.2.7: Update position (entry_price, quantity, notes)"""
        # Arrange
        position = self.db.add_position(
            portfolio_id=self.portfolio.id,
            ticker=self.test_ticker,
            entry_date=self.test_entry_date,
            entry_price=self.test_entry_price,
            quantity=self.test_quantity,
            notes="Original notes"
        )
        
        # Act - Update the position
        updated = self.db.update_position(
            position_id=position.id,
            entry_price=160.0,
            quantity=15,
            notes="Updated notes"
        )
        
        # Assert
        assert updated is not None
        assert updated.entry_price == 160.0
        assert updated.quantity == 15
        assert updated.notes == "Updated notes"
        
        # Verify changes in database
        retrieved = self.db.get_position(position.id)
        assert retrieved.entry_price == 160.0
        assert retrieved.quantity == 15
        assert retrieved.notes == "Updated notes"
    
    def test_delete_position_deletes_market_data(self):
        """Test 1.2.8: Delete position (should delete related market_data)"""
        # Arrange - create position with market data
        position = self.db.add_position(
            portfolio_id=self.portfolio.id,
            ticker=self.test_ticker,
            entry_date=self.test_entry_date,
            entry_price=self.test_entry_price,
            quantity=self.test_quantity
        )
        
        # Add market data
        market_data = MarketData(
            ticker=self.test_ticker,
            position_id=position.id,
            last_updated=datetime.now(),
            current_price=155.0
        )
        self.db.session.add(market_data)
        self.db.session.commit()
        
        # Act - delete the position
        self.db.delete_position(position.id)
        
        # Assert - position should be deleted
        assert self.db.get_position(position.id) is None
        
        # Market data should also be deleted (cascading delete)
        market_data_after = self.db.session.query(MarketData).filter_by(position_id=position.id).first()
        assert market_data_after is None
    
    def test_delete_nonexistent_position_handled_gracefully(self):
        """Test 1.2.9: Delete position (non-existent - should handle gracefully)"""
        # This should not raise an exception
        self.db.delete_position(99999)  # Non-existent ID
        
        # If we get here, the test passes (no exception was raised)
        assert True

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
