"""
Initialize Supabase Database with Schema
This script connects to Supabase and creates all necessary tables
"""

import sys
import os

# Add backend directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from db_config import DatabaseConfig
import psycopg2
from psycopg2 import sql
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def read_schema_file():
    """Read the schema.sql file"""
    schema_path = os.path.join(os.path.dirname(__file__), 'database', 'schema.sql')
    try:
        with open(schema_path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        logger.error(f"Error reading schema file: {e}")
        raise

def initialize_supabase_database():
    """Initialize Supabase database with schema"""
    
    logger.info("Starting Supabase database initialization...")
    
    # Get connection parameters
    conn_params = DatabaseConfig.get_psycopg2_connection_params()
    
    logger.info(f"Connecting to Supabase at {conn_params.get('host', 'N/A')}...")
    
    try:
        # Connect to database
        conn = psycopg2.connect(**conn_params)
        conn.autocommit = False
        cursor = conn.cursor()
        
        logger.info("✓ Connected to Supabase successfully!")
        
        # Read schema file
        logger.info("Reading schema file...")
        schema_sql = read_schema_file()
        
        # Execute schema
        logger.info("Executing schema SQL...")
        cursor.execute(schema_sql)
        conn.commit()
        
        logger.info("✓ Schema executed successfully!")
        
        # Verify tables were created
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
            ORDER BY table_name;
        """)
        
        tables = cursor.fetchall()
        logger.info(f"\n✓ Created {len(tables)} tables:")
        for table in tables:
            logger.info(f"  - {table[0]}")
        
        # Count sample data
        cursor.execute("SELECT COUNT(*) FROM users;")
        user_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM subjects;")
        subject_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM tasks;")
        task_count = cursor.fetchone()[0]
        
        logger.info(f"\n✓ Sample data inserted:")
        logger.info(f"  - Users: {user_count}")
        logger.info(f"  - Subjects: {subject_count}")
        logger.info(f"  - Tasks: {task_count}")
        
        cursor.close()
        conn.close()
        
        logger.info("\n🎉 Supabase database initialized successfully!")
        logger.info("You can now run the application with: python backend/main.py")
        
        return True
        
    except psycopg2.Error as e:
        logger.error(f"\n❌ Database error: {e}")
        if conn:
            conn.rollback()
        return False
    except Exception as e:
        logger.error(f"\n❌ Unexpected error: {e}")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("Smart Study Planner - Supabase Database Initialization")
    print("=" * 60)
    print()
    
    # Check if using PostgreSQL
    if DatabaseConfig.DB_TYPE != 'postgresql':
        logger.error("❌ DB_TYPE must be set to 'postgresql' in .env file")
        logger.info("Please update your .env file and try again.")
        sys.exit(1)
    
    # Initialize database
    success = initialize_supabase_database()
    
    if success:
        print("\n" + "=" * 60)
        print("✓ Setup Complete!")
        print("=" * 60)
        sys.exit(0)
    else:
        print("\n" + "=" * 60)
        print("❌ Setup Failed - Please check the errors above")
        print("=" * 60)
        sys.exit(1)
