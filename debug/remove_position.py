import sys
import os

# Add parent directory to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import DatabaseManager
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def remove_position(position_id):
    try:
        db = DatabaseManager()
        
        # Get position details for logging
        positions = db.get_all_positions()
        position = next((p for p in positions if p.id == position_id), None)
        
        if position:
            logger.info(f"Found position to remove: {position.ticker} (ID: {position.id})")
            db.delete_position(position_id)
            logger.info(f"Successfully removed position {position.ticker}")
        else:
            logger.error(f"No position found with ID {position_id}")
            
    except Exception as e:
        logger.error(f"Error removing position: {str(e)}")
    finally:
        if 'db' in locals():
            db.close()

if __name__ == "__main__":
    # Remove position ID 2 (REI.UN.TO)
    remove_position(2) 