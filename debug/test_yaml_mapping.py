import sys
import os

# Add parent directory to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import DatabaseManager
from yaml_exporter import StockDataYAMLExporter
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def test_yaml_mapping():
    try:
        # Initialize database and exporter
        db = DatabaseManager()
        exporter = StockDataYAMLExporter()
        
        # Get all positions
        positions = db.get_all_positions()
        logger.info("\nCurrent positions in database:")
        for p in positions:
            logger.info(f"ID={p.id}, Ticker={p.ticker}, Entry Price=${p.entry_price}")
            
            # Test YAML generation with correct mapping
            logger.info(f"\nTesting YAML generation for {p.ticker} with correct portfolio ID {p.id}")
            yaml_data = exporter.generate_stock_yaml(p.ticker, p.id)
            
            # Test with mismatched ticker
            if p.ticker != "AAPL":
                logger.info(f"\nTesting YAML generation with mismatched ticker (AAPL) and portfolio ID {p.id}")
                yaml_data_mismatch = exporter.generate_stock_yaml("AAPL", p.id)
            
            # Test with no portfolio ID
            logger.info(f"\nTesting YAML generation for {p.ticker} with no portfolio ID")
            yaml_data_no_id = exporter.generate_stock_yaml(p.ticker)
            
            logger.info("-" * 80)
            
    except Exception as e:
        logger.error(f"Error in test: {str(e)}")
    finally:
        db.close()

if __name__ == "__main__":
    test_yaml_mapping() 