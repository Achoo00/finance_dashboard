import sys
import os

# Add parent directory to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import DatabaseManager
from yaml_exporter import StockDataYAMLExporter

def test_yaml_export():
    # Initialize database and exporter
    db = DatabaseManager()
    exporter = StockDataYAMLExporter()
    
    try:
        # Get AAPL position
        positions = db.get_all_positions()
        aapl = next((p for p in positions if p.ticker == 'AAPL'), None)
        
        if not aapl:
            print("AAPL position not found")
            return
            
        print(f"Found AAPL position: ID={aapl.id}, Entry Price=${aapl.entry_price}")
        
        # Get market data
        market_data = db.get_market_data(aapl.id)
        if market_data:
            print(f"Found market data: Current Price=${market_data.current_price}")
        else:
            print("No market data found")
            
        # Generate YAML
        yaml_data = exporter.generate_stock_yaml('AAPL', aapl.id)
        
        # Write to file in debug folder
        output_path = os.path.join(os.path.dirname(__file__), 'aapl_test.yaml')
        with open(output_path, 'w') as f:
            f.write(yaml_data)
            
        print(f"\nYAML data written to {output_path}")
        
    except Exception as e:
        print(f"Error: {str(e)}")
    finally:
        db.close()

if __name__ == "__main__":
    test_yaml_export() 