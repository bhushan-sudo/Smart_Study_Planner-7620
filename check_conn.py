
import sys
import os
import psycopg2
from db_config import DatabaseConfig

def check_connection():
    print(f"Checking connection to database...")
    params = DatabaseConfig.get_psycopg2_connection_params()
    
    # Mask password for display
    display_params = params.copy()
    if 'password' in display_params:
        display_params['password'] = '******'
    
    print(f"Params: {display_params}")
    
    try:
        conn = psycopg2.connect(**params)
        print("Successfully connected to the database!")
        
        # Check if tables exist
        cur = conn.cursor()
        cur.execute("SELECT table_name FROM information_schema.tables WHERE table_schema='public';")
        tables = cur.fetchall()
        print(f"Found {len(tables)} tables:")
        for table in tables:
            print(f" - {table[0]}")
            
        cur.close()
        conn.close()
        return True
    except Exception as e:
        print(f"Error connecting to database: {e}")
        return False

if __name__ == "__main__":
    if check_connection():
        sys.exit(0)
    else:
        sys.exit(1)
