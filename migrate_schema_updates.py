"""
Database Migration Script
Updates the database schema to support the new frontend features
"""

import psycopg2
from psycopg2.extras import RealDictCursor
import os
from datetime import datetime

def get_db_config():
    """Get database configuration from environment or defaults"""
    return {
        'host': os.getenv('DB_HOST', 'db.voifjwkpgmzjbanvtqdc.supabase.co'),
        'port': os.getenv('DB_PORT', '5432'),
        'database': os.getenv('DB_NAME', 'postgres'),
        'user': os.getenv('DB_USER', 'postgres'),
        'password': os.getenv('DB_PASSWORD', 'your_password_here')
    }

def run_migration():
    """Run database migration"""
    config = get_db_config()

    try:
        # Connect to database
        conn = psycopg2.connect(**config)
        conn.autocommit = True
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        print("Connected to database. Running migrations...")

        # Migration 1: Make task_id nullable in study_sessions
        print("Migration 1: Updating study_sessions table...")
        cursor.execute("""
            ALTER TABLE study_sessions
            ALTER COLUMN task_id DROP NOT NULL,
            ADD COLUMN session_type VARCHAR(50) DEFAULT 'study'
        """)

        # Migration 2: Make task_id nullable in file_attachments
        print("Migration 2: Updating file_attachments table...")
        cursor.execute("""
            ALTER TABLE file_attachments
            ALTER COLUMN task_id DROP NOT NULL
        """)

        # Migration 3: Add any missing indexes
        print("Migration 3: Adding indexes...")
        try:
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_study_sessions_user_id ON study_sessions(user_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_file_attachments_user_id ON file_attachments(user_id)")
        except Exception as e:
            print(f"Index creation warning: {e}")

        print("Migrations completed successfully!")

        # Verify the changes
        print("\nVerifying changes...")
        cursor.execute("""
            SELECT column_name, is_nullable, data_type
            FROM information_schema.columns
            WHERE table_name = 'study_sessions' AND column_name IN ('task_id', 'session_type')
            ORDER BY column_name
        """)
        study_sessions_cols = cursor.fetchall()

        cursor.execute("""
            SELECT column_name, is_nullable, data_type
            FROM information_schema.columns
            WHERE table_name = 'file_attachments' AND column_name = 'task_id'
        """)
        file_attachments_cols = cursor.fetchall()

        print("study_sessions.task_id:", study_sessions_cols[0] if study_sessions_cols else "Not found")
        print("study_sessions.session_type:", study_sessions_cols[1] if len(study_sessions_cols) > 1 else "Not found")
        print("file_attachments.task_id:", file_attachments_cols[0] if file_attachments_cols else "Not found")

        cursor.close()
        conn.close()

        print("\nMigration completed successfully!")

    except Exception as e:
        print(f"Migration failed: {e}")
        return False

    return True

if __name__ == "__main__":
    print("Database Migration Script")
    print("=" * 50)
    print(f"Started at: {datetime.now()}")

    success = run_migration()

    if success:
        print("\n✅ All migrations completed successfully!")
    else:
        print("\n❌ Migration failed!")
        exit(1)