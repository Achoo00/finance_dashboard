import sqlite3
import pandas as pd
from collections.abc import Iterable

def view_database_tables():
    # Connect to the SQLite database
    conn = sqlite3.connect('portfolio.db')
    cursor = conn.cursor()
    
    # Get all table names
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    
    print("\n=== Database Tables ===")
    for table in tables:
        table_name = table[0]
        print(f"\n📋 Table: {table_name}")
        
        # Get table schema
        cursor.execute(f"PRAGMA table_info({table_name});")
        columns = cursor.fetchall()
        
        # Print table structure
        print("\nTable Structure:")
        schema_df = pd.DataFrame(columns, columns=['cid', 'name', 'type', 'notnull', 'dflt_value', 'pk'])
        print("\nColumns:")
        for _, row in schema_df[['name', 'type', 'notnull', 'pk']].iterrows():
            print(f"- {row['name']} ({row['type']}) {'NOT NULL' if row['notnull'] else ''} {'PRIMARY KEY' if row['pk'] else ''}")
        
        # Get and print table contents
        try:
            df = pd.read_sql_query(f"SELECT * FROM {table_name}", conn)
            if not df.empty:
                print("\nTable Contents:")
                print(df.to_string(index=False))
            else:
                print("\nTable is empty")
        except Exception as e:
            print(f"Error reading table contents: {str(e)}")
        
        print("\n" + "="*50)
    
    conn.close()

if __name__ == "__main__":
    try:
        view_database_tables()
    except sqlite3.Error as e:
        print(f"Error connecting to database: {str(e)}")
    except Exception as e:
        print(f"An error occurred: {str(e)}")