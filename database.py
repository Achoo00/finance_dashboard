from sqlalchemy import create_engine, Column, Integer, Float, String, DateTime, ForeignKey, Boolean, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
import json

Base = declarative_base()

class Portfolio(Base):
    __tablename__ = 'portfolio'
    
    id = Column(Integer, primary_key=True)
    ticker = Column(String(10), nullable=False)
    entry_date = Column(DateTime, nullable=False)
    entry_price = Column(Float, nullable=False)
    quantity = Column(Integer, nullable=False)
    notes = Column(Text)
    
    # Relationship with market data
    market_data = relationship("MarketData", back_populates="portfolio", uselist=False)

class MarketData(Base):
    __tablename__ = 'market_data'
    
    id = Column(Integer, primary_key=True)
    ticker = Column(String(10), nullable=False)
    portfolio_id = Column(Integer, ForeignKey('portfolio.id'))
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
    
    # Relationship with portfolio
    portfolio = relationship("Portfolio", back_populates="market_data")

class DatabaseManager:
    def __init__(self, db_path='sqlite:///portfolio.db'):
        self.engine = create_engine(db_path)
        Base.metadata.create_all(self.engine)
        Session = sessionmaker(bind=self.engine)
        self.session = Session()
    
    def add_position(self, ticker, entry_date, entry_price, quantity, notes=None):
        position = Portfolio(
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
        position = self.session.query(Portfolio).filter_by(id=position_id).first()
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
    
    def delete_position(self, position_id):
        position = self.session.query(Portfolio).filter_by(id=position_id).first()
        if position:
            self.session.delete(position)
            self.session.commit()
            return True
        return False
    
    def get_all_positions(self):
        return self.session.query(Portfolio).all()
    
    def update_market_data(self, portfolio_id, market_data, technical_data=None):
        """Update market data for a position"""
        existing = self.session.query(MarketData).filter_by(portfolio_id=portfolio_id).first()
        
        if not existing:
            existing = MarketData(portfolio_id=portfolio_id)
            self.session.add(existing)
        
        # Update market data fields
        for key, value in market_data.items():
            if key in ['quarterly_revenue', 'quarterly_net_income']:
                if value:
                    setattr(existing, key, json.dumps(value))
            else:
                setattr(existing, key, value)
        
        # Update technical indicators if provided
        if technical_data:
            for key, value in technical_data.items():
                setattr(existing, key, value)
        
        existing.last_updated = datetime.now()
        existing.ticker = self.session.query(Portfolio).filter_by(id=portfolio_id).first().ticker
        
        self.session.commit()
        return existing
    
    def get_market_data(self, portfolio_id):
        """Get market data for a position"""
        return self.session.query(MarketData).filter_by(portfolio_id=portfolio_id).first()
    
    def close(self):
        """Close the database session"""
        self.session.close() 