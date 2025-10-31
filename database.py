from sqlalchemy import create_engine, Column, Integer, Float, String, DateTime, ForeignKey, Boolean, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
import json
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

Base = declarative_base()

class Portfolio(Base):
    __tablename__ = 'portfolios'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False, unique=True)
    description = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    is_default = Column(Boolean, default=False)
    
    # Relationship with positions
    positions = relationship("Position", back_populates="portfolio", cascade="all, delete-orphan")

class Position(Base):
    __tablename__ = 'positions'
    
    id = Column(Integer, primary_key=True)
    portfolio_id = Column(Integer, ForeignKey('portfolios.id', ondelete='CASCADE'), nullable=False)
    ticker = Column(String(10), nullable=False)
    entry_date = Column(DateTime, nullable=False)
    entry_price = Column(Float, nullable=False)
    quantity = Column(Integer, nullable=False)
    notes = Column(Text)
    
    # Relationships
    portfolio = relationship("Portfolio", back_populates="positions")
    market_data = relationship("MarketData", back_populates="position", uselist=False)

class MarketData(Base):
    __tablename__ = 'market_data'
    
    id = Column(Integer, primary_key=True)
    ticker = Column(String(10), nullable=False)
    position_id = Column(Integer, ForeignKey('positions.id', ondelete='CASCADE'))
    last_updated = Column(DateTime, nullable=False)
    
    # Market data
    current_price = Column(Float)
    day_low = Column(Float)
    day_high = Column(Float)
    fifty_two_week_low = Column(Float)
    fifty_two_week_high = Column(Float)
    volume = Column(Integer)
    avg_volume = Column(Integer)
    market_cap = Column(Float)
    
    # Fundamentals
    pe_ratio = Column(Float)
    forward_pe = Column(Float)
    eps = Column(Float)
    profit_margin = Column(Float)
    dividend_yield = Column(Float)
    next_earnings_date = Column(DateTime)
    
    # Technical indicators
    rsi = Column(Float)
    macd = Column(Float)
    macd_signal = Column(Float)
    sma_50 = Column(Float)
    sma_200 = Column(Float)
    is_above_50_sma = Column(Boolean)
    is_above_200_sma = Column(Boolean)
    rsi_overbought = Column(Boolean)
    rsi_oversold = Column(Boolean)
    macd_crossover = Column(Boolean)
    
    # Store quarterly financials as JSON
    quarterly_revenue = Column(Text)  # JSON string
    quarterly_net_income = Column(Text)  # JSON string
    
    # Relationship with position
    position = relationship("Position", back_populates="market_data")

class PriceHistory(Base):
    __tablename__ = 'price_history'
    id = Column(Integer, primary_key=True)
    ticker = Column(String(10), nullable=False)
    date = Column(DateTime, nullable=False)
    open = Column(Float)
    high = Column(Float)
    low = Column(Float)
    close = Column(Float)
    volume = Column(Integer)
    # Optionally, add adj_close if needed
    
    def as_dict(self):
        return {
            'ticker': self.ticker,
            'date': self.date,
            'open': self.open,
            'high': self.high,
            'low': self.low,
            'close': self.close,
            'volume': self.volume
        }

class Financials(Base):
    __tablename__ = 'financials'
    id = Column(Integer, primary_key=True)
    ticker = Column(String(10), nullable=False)
    period = Column(String(20), nullable=False)  # e.g., '2024Q1'
    revenue = Column(Float)
    net_income = Column(Float)
    eps = Column(Float)
    profit_margin = Column(Float)
    dividend_yield = Column(Float)
    # Add more fields as needed

class DatabaseManager:
    def __init__(self, db_path='sqlite:///portfolio.db'):
        logger.info("Initializing DatabaseManager")
        self.engine = create_engine(db_path)
        Base.metadata.create_all(self.engine)
        Session = sessionmaker(bind=self.engine)
        self.session = Session()
    
    def add_position(self, portfolio_id, ticker, entry_date, entry_price, quantity, notes=None):
        position = Position(
            portfolio_id=portfolio_id,
            ticker=ticker,
            entry_date=entry_date,
            entry_price=entry_price,
            quantity=quantity,
            notes=notes
        )
        self.session.add(position)
        self.session.commit()
        return position
    
    def update_position(self, position_id, entry_price=None, quantity=None, notes=None):
        """Update a position by ID"""
        position = self.get_position(position_id)
        if position:
            if entry_price is not None:
                position.entry_price = entry_price
            if quantity is not None:
                position.quantity = quantity
            if notes is not None:
                position.notes = notes
            self.session.commit()
            return position
        return None
    
    def get_all_positions(self):
        """Get all positions from all portfolios"""
        return self.session.query(Position).all()
    
    def update_market_data(self, position_id, market_data, technical_data=None):
        """Update market data for a position"""
        position = self.get_position(position_id)
        if not position:
            logger.error(f"Position with ID {position_id} not found")
            return None
            
        existing = self.session.query(MarketData).filter_by(position_id=position_id).first()
        ticker = position.ticker if position else None
        
        if not existing:
            existing = MarketData(position_id=position_id, ticker=ticker)
            self.session.add(existing)
            
        # Update market data fields
        for key, value in market_data.items():
            if key in ['quarterly_revenue', 'quarterly_net_income']:
                if value:
                    setattr(existing, key, json.dumps(value))
            elif hasattr(existing, key):
                setattr(existing, key, value)
                
        # Update technical indicators if provided
        if technical_data:
            for key, value in technical_data.items():
                if hasattr(existing, key):
                    setattr(existing, key, value)
                    
        existing.last_updated = datetime.now()
        existing.ticker = ticker
        self.session.commit()
        return existing
    
    
    def get_position(self, position_id):
        """Get a position by ID"""
        logger.info(f"Getting position with ID: {position_id}")
        try:
            position = self.session.query(Position).filter_by(id=position_id).first()
            logger.info(f"Found position: {position is not None}")
            return position
        except Exception as e:
            logger.error(f"Error getting position: {str(e)}")
            return None
    
    def add_price_history(self, ticker, price_data):
        """Add or update price history for a ticker. price_data: list of dicts with keys: date, open, high, low, close, volume"""
        for row in price_data:
            ph = PriceHistory(
                ticker=ticker,
                date=row['date'],
                open=row.get('open'),
                high=row.get('high'),
                low=row.get('low'),
                close=row.get('close'),
                volume=row.get('volume')
            )
            self.session.merge(ph)
        self.session.commit()

    def get_price_history(self, ticker, start_date=None, end_date=None):
        q = self.session.query(PriceHistory).filter_by(ticker=ticker)
        if start_date:
            q = q.filter(PriceHistory.date >= start_date)
        if end_date:
            q = q.filter(PriceHistory.date <= end_date)
        return [row.as_dict() for row in q.order_by(PriceHistory.date).all()]

    def add_financials(self, ticker, period, revenue=None, net_income=None, eps=None, profit_margin=None, dividend_yield=None):
        fin = Financials(
            ticker=ticker,
            period=period,
            revenue=revenue,
            net_income=net_income,
            eps=eps,
            profit_margin=profit_margin,
            dividend_yield=dividend_yield
        )
        self.session.merge(fin)
        self.session.commit()

    def get_financials(self, ticker, period=None):
        q = self.session.query(Financials).filter_by(ticker=ticker)
        if period:
            q = q.filter_by(period=period)
        return q.all()
    
    # Portfolio management methods
    def create_portfolio(self, name, description=None, is_default=False):
        """Create a new portfolio"""
        if is_default:
            # Reset any existing default
            self.session.query(Portfolio).update({"is_default": False})
            
        portfolio = Portfolio(
            name=name,
            description=description,
            is_default=is_default
        )
        self.session.add(portfolio)
        self.session.commit()
        return portfolio
    
    def get_portfolio(self, portfolio_id):
        """Get a portfolio by ID"""
        return self.session.query(Portfolio).filter_by(id=portfolio_id).first()
    
    def get_all_portfolios(self):
        """Get all portfolios"""
        return self.session.query(Portfolio).order_by(Portfolio.name).all()
    
    def get_default_portfolio(self):
        """Get the default portfolio"""
        return self.session.query(Portfolio).filter_by(is_default=True).first() or \
               self.session.query(Portfolio).first()
    
    def update_portfolio(self, portfolio_id, name=None, description=None, is_default=None):
        """Update a portfolio"""
        portfolio = self.get_portfolio(portfolio_id)
        if not portfolio:
            return None
            
        if is_default and not portfolio.is_default:
            # Reset any existing default
            self.session.query(Portfolio).update({"is_default": False})
            
        if name is not None:
            portfolio.name = name
        if description is not None:
            portfolio.description = description
        if is_default is not None:
            portfolio.is_default = is_default
            
        self.session.commit()
        return portfolio
    
    def delete_portfolio(self, portfolio_id):
        """Delete a portfolio and all its positions"""
        portfolio = self.get_portfolio(portfolio_id)
        if portfolio:
            self.session.delete(portfolio)
            self.session.commit()
    def get_portfolio_positions(self, portfolio_id):
        return self.session.query(Position).filter_by(portfolio_id=portfolio_id).all()
        
    def get_market_data(self, position_id):
        """Get market data for a position"""
        logger.info(f"Getting market data for position ID: {position_id}")
        try:
            market_data = self.session.query(MarketData).filter_by(position_id=position_id).first()
            logger.info(f"Found market data: {market_data is not None}")
            if market_data:
                logger.info(f"Market data values: price={market_data.current_price}, volume={market_data.volume}")
            return market_data
        except Exception as e:
            logger.error(f"Error getting market data: {str(e)}")
            return None
            
    def delete_position(self, position_id):
        """Delete a position and its related market data"""
        try:
            # Delete related market data first (if exists)
            market_data = self.get_market_data(position_id)
            if market_data:
                self.session.delete(market_data)
                
            # Delete the position
            position = self.get_position(position_id)
            if position:
                self.session.delete(position)
                self.session.commit()
                return True
            else:
                logger.warning(f"Position with ID {position_id} not found")
                return False
        except Exception as e:
            self.session.rollback()
            logger.error(f"Error deleting position {position_id}: {str(e)}")
            return False
    
    def close(self):
        """Close the database session"""
        self.session.close()