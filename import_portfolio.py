import pandas as pd
from database import DatabaseManager
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def import_portfolio():
    try:
        # Read the CSV file
        df = pd.read_csv('portfolio_export.csv')
        logger.info(f"Read {len(df)} positions from CSV")
        
        # Connect to database
        db = DatabaseManager()
        
        # Import each position
        for _, row in df.iterrows():
            try:
                # Convert entry_date string to datetime
                entry_date = datetime.strptime(row['entry_date'].strip(), '%Y-%m-%d %H:%M:%S')
                
                # Add position to database
                position_id = db.add_position(
                    ticker=row['ticker'].strip(),
                    entry_date=entry_date,
                    entry_price=float(row['entry_price']),
                    quantity=int(row['quantity']),
                    notes=row['notes'].strip() if pd.notna(row['notes']) else None
                )
                
                logger.info(f"Added position: {row['ticker']} (ID: {position_id})")
                
            except Exception as e:
                logger.error(f"Error adding position {row['ticker']}: {str(e)}")
                continue
        
        logger.info("Portfolio import completed")
        
    except Exception as e:
        logger.error(f"Error importing portfolio: {str(e)}")
    finally:
        if 'db' in locals():
            db.close()

if __name__ == "__main__":
    import_portfolio() 