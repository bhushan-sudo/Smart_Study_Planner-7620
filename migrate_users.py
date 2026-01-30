
import sys
import psycopg2
from db_config import DatabaseConfig

def migrate():
    print("Running migration: Add profile_image_url to users table...")
    params = DatabaseConfig.get_psycopg2_connection_params()
    
    try:
        conn = psycopg2.connect(**params)
        cur = conn.cursor()
        
        # Check if column exists
        cur.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name='users' AND column_name='profile_image_url';
        """)
        
        if cur.fetchone():
            print("Column 'profile_image_url' already exists.")
        else:
            print("Adding 'profile_image_url' column...")
            cur.execute("ALTER TABLE users ADD COLUMN profile_image_url TEXT;")
            conn.commit()
            print("Migration successful: Column added.")
            
        cur.close()
        conn.close()
        return True
    except Exception as e:
        print(f"Migration failed: {e}")
        return False

if __name__ == "__main__":
    if migrate():
        sys.exit(0)
    else:
        sys.exit(1)
