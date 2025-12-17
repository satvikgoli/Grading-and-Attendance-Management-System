import sqlite3
import os

# Get absolute path for database file
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DB_PATH = os.path.join(BASE_DIR, 'instance', 'GAMS_database.db')

# Create instance directory if it doesn't exist
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

# Try to create and connect to the database
try:
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Create a test table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS test (
            id INTEGER PRIMARY KEY,
            name TEXT
        )
    ''')
    
    # Insert a test record
    cursor.execute('INSERT INTO test (name) VALUES (?)', ('test',))
    
    # Commit the changes
    conn.commit()
    
    # Query the test table
    cursor.execute('SELECT * FROM test')
    result = cursor.fetchall()
    print("Test successful! Database created and accessed.")
    print("Test query result:", result)
    
except Exception as e:
    print(f"Error: {e}")
finally:
    if 'conn' in locals():
        conn.close() 