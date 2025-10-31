import sys
import os
from datetime import datetime

# Add parent directory to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import DatabaseManager
from data_collector import StockDataCollector
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def update_market_data(ticker):
    try:
        db = DatabaseManager()
        collector = StockDataCollector()
        
        # Get position details
        positions = db.get_all_positions()
        position = next((p for p in positions if p.ticker == ticker), None)
        
        if position:
            logger.info(f"Updating market data for {ticker} (ID: {position.id})")
            
            # Get fresh data
            fresh_data = collector.get_stock_data(ticker)
            if fresh_data:
                # If current_price is None but we have day_high, use that
                if not fresh_data.get('current_price') and fresh_data.get('day_high'):
                    fresh_data['current_price'] = fresh_data['day_high']
                    logger.info(f"Using day_high (${fresh_data['day_high']}) as current price")
                
                # Update market data
                db.update_market_data(position.id, fresh_data)
                logger.info(f"Successfully updated market data for {ticker}")
                
                # Verify update
                updated_data = db.get_market_data(position.id)
                logger.info(f"New current price: ${updated_data.current_price}")
            else:
                logger.error("Could not fetch fresh data")
        else:
            logger.error(f"No position found for {ticker}")
            
    except Exception as e:
        logger.error(f"Error updating market data: {str(e)}")
    finally:
        if 'db' in locals():
            db.close()

if __name__ == "__main__":
    update_market_data('XEQT.TO') 