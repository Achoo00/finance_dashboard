from database import DatabaseManager
from datetime import datetime

def init_database():
    try:
        # Create database manager instance
        db = DatabaseManager()
        
        # Add a test position
        pos = db.add_position(
            ticker='AAPL',
            entry_date=datetime.now(),
            entry_price=170.50,
            quantity=10,
            notes='Test position'
        )
        
        print('Database initialized and test position added successfully')
        
    except Exception as e:
        print(f'Error initializing database: {str(e)}')
    finally:
        if 'db' in locals():
            db.close()

if __name__ == '__main__':
    init_database() 