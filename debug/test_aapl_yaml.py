import sys
import os

# Add parent directory to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from yaml_exporter import StockDataYAMLExporter
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def test_aapl_yaml():
    try:
        # Initialize exporter
        exporter = StockDataYAMLExporter()
        
        # Test YAML generation for AAPL with portfolio ID 1
        logger.info("Testing YAML generation for AAPL with portfolio ID 1")
        yaml_data = exporter.generate_stock_yaml("AAPL", 1)
        
        # Print the YAML data
        print("\nGenerated YAML for AAPL:")
        print("=" * 80)
        print(yaml_data)
        print("=" * 80)
        
    except Exception as e:
        logger.error(f"Error in test: {str(e)}")

if __name__ == "__main__":
    test_aapl_yaml() 