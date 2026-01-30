"""
Initialize AI Agent Database Schema
Run this script to create the chat_messages table
"""

import sys
import os

# Add backend directory to path
backend_path = os.path.join(os.path.dirname(__file__), 'backend')
sys.path.insert(0, backend_path)

from database import Database
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def init_agent_schema():
    """Initialize the agent database schema"""
    
    schema_sql = """
    -- AI Agent Chat Messages Table
    CREATE TABLE IF NOT EXISTS chat_messages (
        message_id SERIAL PRIMARY KEY,
        user_id INTEGER NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
        role VARCHAR(20) NOT NULL CHECK (role IN ('user', 'assistant', 'system')),
        content TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    -- Create indexes for better query performance
    CREATE INDEX IF NOT EXISTS idx_chat_user ON chat_messages(user_id);
    CREATE INDEX IF NOT EXISTS idx_chat_created ON chat_messages(created_at);
    CREATE INDEX IF NOT EXISTS idx_chat_user_created ON chat_messages(user_id, created_at DESC);
    """
    
    try:
        logger.info("Creating chat_messages table...")
        Database.execute_query(schema_sql, fetch=False)
        logger.info("✓ Agent schema initialized successfully!")
        
        # Verify table was created
        verify_query = """
            SELECT table_name FROM information_schema.tables 
            WHERE table_schema = 'public' AND table_name = 'chat_messages'
        """
        result = Database.fetch_one(verify_query)
        
        if result:
            logger.info("✓ chat_messages table verified")
        else:
            logger.error("✗ chat_messages table not found after creation")
            
    except Exception as e:
        logger.error(f"Error initializing agent schema: {e}")
        raise

if __name__ == '__main__':
    init_agent_schema()
