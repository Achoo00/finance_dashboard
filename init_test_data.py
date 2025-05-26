from database import DatabaseManager
from datetime import datetime, timedelta
import random

def init_test_portfolio():
    try:
        # Create database manager instance
        db = DatabaseManager()
        
        # Test portfolio with diverse stocks
        test_positions = [
            {
                'ticker': 'AAPL',
                'entry_date': datetime.now() - timedelta(days=180),
                'entry_price': 165.50,
                'quantity': 15,
                'notes': 'Core tech holding',
                'market_cap': 2.95e12,  # $2.95 trillion
                'market_value': 175.25  # Current market price
            },
            {
                'ticker': 'MSFT',
                'entry_date': datetime.now() - timedelta(days=90),
                'entry_price': 325.75,
                'quantity': 10,
                'notes': 'Cloud and AI exposure',
                'market_cap': 3.05e12,  # $3.05 trillion
                'market_value': 337.50  # Current market price
            },
            {
                'ticker': 'GOOGL',
                'entry_date': datetime.now() - timedelta(days=120),
                'entry_price': 125.30,
                'quantity': 20,
                'notes': 'Digital advertising leader',
                'market_cap': 1.85e12,  # $1.85 trillion
                'market_value': 131.75  # Current market price
            },
            {
                'ticker': 'NVDA',
                'entry_date': datetime.now() - timedelta(days=60),
                'entry_price': 420.50,
                'quantity': 8,
                'notes': 'AI and gaming growth',
                'market_cap': 1.15e12,  # $1.15 trillion
                'market_value': 445.75  # Current market price
            },
            {
                'ticker': 'JPM',
                'entry_date': datetime.now() - timedelta(days=150),
                'entry_price': 145.25,
                'quantity': 25,
                'notes': 'Banking sector exposure',
                'market_cap': 4.35e11,  # $435 billion
                'market_value': 152.50  # Current market price
            }
        ]
        
        # Add positions to database
        positions_added = 0
        for position in test_positions:
            try:
                # Add the position
                pos = db.add_position(
                    ticker=position['ticker'],
                    entry_date=position['entry_date'],
                    entry_price=position['entry_price'],
                    quantity=position['quantity'],
                    notes=position['notes']
                )
                
                if pos:
                    positions_added += 1
                    print(f"Added {position['ticker']} position successfully")
                    
                    # Calculate price change percentage for consistent data
                    price_change = (position['market_value'] / position['entry_price']) - 1
                    
                    # Add some mock market data
                    mock_market_data = {
                        'ticker': position['ticker'],
                        'current_price': position['market_value'],
                        'day_low': position['market_value'] * 0.98,
                        'day_high': position['market_value'] * 1.02,
                        'fifty_two_week_low': position['market_value'] * 0.8,
                        'fifty_two_week_high': position['market_value'] * 1.3,
                        'volume': random.randint(1000000, 10000000),
                        'avg_volume': random.randint(2000000, 8000000),
                        'market_cap': position['market_cap'],
                        'pe_ratio': random.uniform(15, 35),
                        'forward_pe': random.uniform(14, 30),
                        'eps': position['market_value'] / random.uniform(20, 30),  # P/E based EPS
                        'profit_margin': random.uniform(0.15, 0.35),
                        'dividend_yield': random.uniform(0.005, 0.025),
                        'next_earnings_date': datetime.now() + timedelta(days=random.randint(10, 60))
                    }
                    
                    # Add mock technical indicators
                    mock_technical_data = {
                        'rsi': random.uniform(30, 70),
                        'macd': random.uniform(-2, 2),
                        'macd_signal': random.uniform(-2, 2),
                        'sma_50': position['market_value'] * (1 + random.uniform(-0.05, 0.05)),
                        'sma_200': position['market_value'] * (1 + random.uniform(-0.1, 0.1)),
                        'is_above_50_sma': price_change > 0,
                        'is_above_200_sma': price_change > 0.05,
                        'rsi_overbought': False,
                        'rsi_oversold': False,
                        'macd_crossover': random.choice([True, False])
                    }
                    
                    # Update market data with both market and technical data
                    db.update_market_data(pos.id, mock_market_data, mock_technical_data)
                    print(f"Added market data for {position['ticker']}")
                
            except Exception as e:
                print(f"Error adding {position['ticker']}: {str(e)}")
                db.session.rollback()  # Rollback on error
        
        print(f"\nSuccessfully added {positions_added} test positions to the portfolio")
        
    except Exception as e:
        print(f"Error initializing database: {str(e)}")
    finally:
        if 'db' in locals():
            db.close()

if __name__ == '__main__':
    init_test_portfolio() 