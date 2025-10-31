import sys
import os
import sqlite3

# Add parent directory to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import DatabaseManager
import logging
from sqlalchemy import text

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def cleanup_market_data():
    db = DatabaseManager()
    
    try:
        with db.session as session:
            # First, get all valid positions
            positions = session.execute(text("""
                SELECT id, ticker 
                FROM portfolio 
                ORDER BY id
            """)).fetchall()
            
            valid_position_ids = {p[0]: p[1] for p in positions}
            logger.info("Valid positions in database:")
            for pid, ticker in valid_position_ids.items():
                logger.info(f"Position ID={pid}, Ticker={ticker}")

            # Delete any market data entries with null portfolio_id
            logger.info("\nRemoving market data entries with null portfolio_id...")
            result = session.execute(text("DELETE FROM market_data WHERE portfolio_id IS NULL"))
            logger.info(f"Removed {result.rowcount} entries with null portfolio_id")

            # Get current market data entries
            logger.info("\nCurrent market data entries:")
            market_data = session.execute(text("""
                SELECT id, portfolio_id, ticker, last_updated, current_price 
                FROM market_data 
                ORDER BY portfolio_id, last_updated DESC
            """)).fetchall()
            
            for row in market_data:
                logger.info(f"ID={row[0]}, Portfolio ID={row[1]}, Ticker={row[2]}, Last Updated={row[3]}, Price=${row[4]}")

            # Find and remove duplicate entries (keeping the most recent for each portfolio_id)
            logger.info("\nFinding duplicate entries...")
            duplicates = session.execute(text("""
                WITH RankedData AS (
                    SELECT 
                        id,
                        portfolio_id,
                        ticker,
                        last_updated,
                        ROW_NUMBER() OVER (PARTITION BY portfolio_id ORDER BY last_updated DESC) as rn
                    FROM market_data
                    WHERE portfolio_id IS NOT NULL
                )
                SELECT id, portfolio_id, ticker, last_updated
                FROM RankedData
                WHERE rn > 1
                ORDER BY portfolio_id, last_updated DESC
            """)).fetchall()

            if duplicates:
                logger.info(f"Found {len(duplicates)} duplicate entries to remove:")
                for dup in duplicates:
                    logger.info(f"ID={dup[0]}, Portfolio ID={dup[1]}, Ticker={dup[2]}, Last Updated={dup[3]}")
                    session.execute(text("DELETE FROM market_data WHERE id = :id"), {"id": dup[0]})
                logger.info("Successfully removed duplicate entries")
            else:
                logger.info("No duplicate market data entries found!")

            # Remove any market data entries for non-existent positions
            logger.info("\nRemoving market data for non-existent positions...")
            result = session.execute(text("""
                DELETE FROM market_data 
                WHERE portfolio_id NOT IN (SELECT id FROM portfolio)
            """))
            logger.info(f"Removed {result.rowcount} entries for non-existent positions")

            session.commit()

            # Verify the cleanup
            logger.info("\nRemaining market data entries:")
            remaining = session.execute(text("""
                SELECT m.id, m.portfolio_id, m.ticker, m.last_updated, m.current_price,
                       p.ticker as position_ticker
                FROM market_data m
                JOIN portfolio p ON m.portfolio_id = p.id
                ORDER BY m.portfolio_id
            """)).fetchall()
            
            for row in remaining:
                logger.info(f"ID={row[0]}, Portfolio ID={row[1]}, Market Data Ticker={row[2]}, "
                          f"Position Ticker={row[5]}, Last Updated={row[3]}, Price=${row[4]}")

            # Verify each position has exactly one market data entry
            logger.info("\nVerifying data integrity:")
            for pid, ticker in valid_position_ids.items():
                count = session.execute(text("""
                    SELECT COUNT(*) FROM market_data WHERE portfolio_id = :pid
                """), {"pid": pid}).scalar()
                logger.info(f"Position ID={pid} ({ticker}) has {count} market data entries")

    except Exception as e:
        logger.error(f"Error cleaning up market data: {str(e)}")
        session.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    cleanup_market_data() 