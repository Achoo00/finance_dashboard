from database import DatabaseManager
from yaml_exporter import StockDataYAMLExporter
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def debug_database():
    db = DatabaseManager()
    exporter = StockDataYAMLExporter()
    
    # Get AAPL position
    positions = db.get_all_positions()
    aapl = next((p for p in positions if p.ticker == 'AAPL'), None)
    
    if aapl:
        logger.info(f"Found AAPL position: ID={aapl.id}, Entry Price=${aapl.entry_price}")
        
        # Get market data
        market_data = db.get_market_data(aapl.id)
        if market_data:
            logger.info(f"Market Data found:")
            for column in market_data.__table__.columns:
                value = getattr(market_data, column.name)
                logger.info(f"  {column.name}: {value}")
        else:
            logger.error("No market data found")
            
        # Try generating YAML
        yaml_data = exporter.generate_stock_yaml('AAPL', aapl.id)
        logger.info("\nGenerated YAML:\n" + yaml_data)
    else:
        logger.error("AAPL position not found")

if __name__ == "__main__":
    debug_database() 