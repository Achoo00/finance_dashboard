import sys
import os
import sqlite3

# Add parent directory to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import DatabaseManager
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def clear_database():
    try:
        # Connect directly to the database
        conn = sqlite3.connect('portfolio.db')
        cursor = conn.cursor()
        
        # Check which tables exist
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [table[0] for table in cursor.fetchall()]
        logger.info(f"Found tables in database: {tables}")
        
        # Delete market data if the table exists
        if 'market_data' in tables:
            cursor.execute("DELETE FROM market_data")
            market_data_count = cursor.rowcount
            logger.info(f"Deleted {market_data_count} market data entries")
        else:
            logger.info("No market_data table found")
            
        # Delete from portfolio table if it exists
        if 'portfolio' in tables:
            cursor.execute("DELETE FROM portfolio")
            portfolio_count = cursor.rowcount
            logger.info(f"Deleted {portfolio_count} portfolio entries")
        else:
            logger.info("No portfolio table found")
            
        # Delete from price_history if it exists
        if 'price_history' in tables:
            cursor.execute("DELETE FROM price_history")
            history_count = cursor.rowcount
            logger.info(f"Deleted {history_count} price history entries")
        else:
            logger.info("No price_history table found")
            
        # Delete from financials if it exists
        if 'financials' in tables:
            cursor.execute("DELETE FROM financials")
            financials_count = cursor.rowcount
            logger.info(f"Deleted {financials_count} financial entries")
        else:
            logger.info("No financials table found")
        
        conn.commit()
        conn.close()
        
        logger.info("Database cleanup completed")
        
    except Exception as e:
        logger.error(f"Error clearing database: {str(e)}")
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    clear_database() 