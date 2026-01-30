"""
Apply Security Policies to Supabase
This script connects to Supabase and runs the secure_database.sql script
"""

import sys
import os

# Add backend directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from db_config import DatabaseConfig
import psycopg2
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def read_security_file():
    """Read the secure_database.sql file"""
    schema_path = os.path.join(os.path.dirname(__file__), 'database', 'secure_database.sql')
    try:
        with open(schema_path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        logger.error(f"Error reading security file: {e}")
        raise

def apply_security_policies():
    """Apply security policies"""
    
    logger.info("Starting security policy application...")
    
    # Get connection parameters
    conn_params = DatabaseConfig.get_psycopg2_connection_params()
    
    try:
        # Connect to database
        conn = psycopg2.connect(**conn_params)
        conn.autocommit = False
        cursor = conn.cursor()
        
        logger.info("✓ Connected to Supabase successfully!")
        
        # Read security file
        logger.info("Reading security policies...")
        security_sql = read_security_file()
        
        # Execute SQL
        logger.info("Applying RLS policies...")
        cursor.execute(security_sql)
        conn.commit()
        
        logger.info("✓ Security policies applied successfully!")
        
        cursor.close()
        conn.close()
        
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
    print("Smart Study Planner - Supabase Security Setup")
    print("=" * 60)
    print()
    
    # Check if using PostgreSQL
    if DatabaseConfig.DB_TYPE != 'postgresql':
        logger.error("❌ DB_TYPE must be set to 'postgresql' in .env file")
        sys.exit(1)
    
    # Apply policies
    success = apply_security_policies()
    
    if success:
        print("\n" + "=" * 60)
        print("✓ Security Setup Complete!")
        print("RLS enabled and policies applied to all tables.")
        print("=" * 60)
        sys.exit(0)
    else:
        print("\n" + "=" * 60)
        print("❌ Setup Failed - Please check the errors above")
        print("=" * 60)
        sys.exit(1)
