import sys
import os

# Add parent directory to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import DatabaseManager
from data_collector import StockDataCollector
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_stock_data(ticker):
    try:
        db = DatabaseManager()
        collector = StockDataCollector()
        
        # Get position details
        positions = db.get_all_positions()
        position = next((p for p in positions if p.ticker == ticker), None)
        
        if position:
            logger.info(f"\nPosition data for {ticker}:")
            logger.info(f"ID: {position.id}")
            logger.info(f"Entry Price: ${position.entry_price}")
            logger.info(f"Quantity: {position.quantity}")
            
            # Get market data from database
            market_data = db.get_market_data(position.id)
            if market_data:
                logger.info(f"\nStored market data:")
                logger.info(f"Current Price: ${market_data.current_price if market_data.current_price else 'NaN'}")
                logger.info(f"Last Updated: {market_data.last_updated}")
            else:
                logger.info("\nNo market data found in database")
            
            # Get fresh data from collector
            logger.info(f"\nFetching fresh data from yfinance:")
            fresh_data = collector.get_stock_data(ticker)
            if fresh_data:
                logger.info(f"Current Price: ${fresh_data.get('current_price')}")
                logger.info(f"Day Range: ${fresh_data.get('day_low')} - ${fresh_data.get('day_high')}")
            else:
                logger.info("Could not fetch fresh data")
                
        else:
            logger.error(f"No position found for {ticker}")
            
    except Exception as e:
        logger.error(f"Error checking stock data: {str(e)}")
    finally:
        if 'db' in locals():
            db.close()

if __name__ == "__main__":
    check_stock_data('XEQT.TO') 