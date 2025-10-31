import sys
import os
import sqlite3

# Add parent directory to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database import DatabaseManager
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def cleanup_duplicates():
    db = DatabaseManager()
    
    # Get all positions
    positions = db.get_all_positions()
    
    # Create a dictionary to track unique tickers
    unique_positions = {}
    duplicates = []
    
    # Find duplicates
    for position in positions:
        if position.ticker not in unique_positions:
            unique_positions[position.ticker] = position
        else:
            duplicates.append(position)
    
    logger.info(f"Found {len(duplicates)} duplicate positions")
    
    # Delete duplicates
    for duplicate in duplicates:
        logger.info(f"Deleting duplicate position: ID={duplicate.id}, Ticker={duplicate.ticker}")
        db.delete_position(duplicate.id)
    
    # Verify cleanup
    remaining = db.get_all_positions()
    logger.info("\nRemaining positions:")
    for position in remaining:
        logger.info(f"ID={position.id}, Ticker={position.ticker}, Entry Price=${position.entry_price}")
    
    db.close()

if __name__ == "__main__":
    cleanup_duplicates() 