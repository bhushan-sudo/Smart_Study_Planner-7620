"""
Database migration script for advanced features
Run this script to add new tables for study goals, streaks, notifications, and file attachments
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from backend.database import Database
from backend.db_config import DatabaseConfig

def run_migration():
    """Run database migration for advanced features"""

    print("Starting database migration for advanced features...")

    # Study Goals table
    create_goals_table = """
    CREATE TABLE IF NOT EXISTS study_goals (
        goal_id SERIAL PRIMARY KEY,
        user_id INTEGER NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
        title VARCHAR(200) NOT NULL,
        description TEXT,
        target_value DECIMAL(8,2) NOT NULL,
        current_value DECIMAL(8,2) DEFAULT 0,
        goal_type VARCHAR(50) NOT NULL,
        target_date DATE NOT NULL,
        status VARCHAR(50) DEFAULT 'active',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """

    # Study Streaks table
    create_streaks_table = """
    CREATE TABLE IF NOT EXISTS study_streaks (
        streak_id SERIAL PRIMARY KEY,
        user_id INTEGER NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
        streak_date DATE NOT NULL,
        study_hours DECIMAL(4,2) DEFAULT 0,
        tasks_completed INTEGER DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(user_id, streak_date)
    );
    """

    # Notifications table
    create_notifications_table = """
    CREATE TABLE IF NOT EXISTS notifications (
        notification_id SERIAL PRIMARY KEY,
        user_id INTEGER NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
        title VARCHAR(200) NOT NULL,
        message TEXT,
        notification_type VARCHAR(50) DEFAULT 'info',
        is_read BOOLEAN DEFAULT FALSE,
        scheduled_for TIMESTAMP,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """

    # File Attachments table
    create_attachments_table = """
    CREATE TABLE IF NOT EXISTS file_attachments (
        attachment_id SERIAL PRIMARY KEY,
        task_id INTEGER REFERENCES tasks(task_id) ON DELETE CASCADE,
        user_id INTEGER NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
        filename VARCHAR(255) NOT NULL,
        file_path VARCHAR(500) NOT NULL,
        file_size INTEGER,
        file_type VARCHAR(100),
        uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """

    # Indexes
    create_indexes = """
    CREATE INDEX IF NOT EXISTS idx_study_goals_user_id ON study_goals(user_id);
    CREATE INDEX IF NOT EXISTS idx_study_streaks_user_id ON study_streaks(user_id);
    CREATE INDEX IF NOT EXISTS idx_notifications_user_id ON notifications(user_id);
    CREATE INDEX IF NOT EXISTS idx_file_attachments_task_id ON file_attachments(task_id);
    """

    try:
        # Execute migrations
        Database.execute_query(create_goals_table)
        print("✓ Created study_goals table")

        Database.execute_query(create_streaks_table)
        print("✓ Created study_streaks table")

        Database.execute_query(create_notifications_table)
        print("✓ Created notifications table")

        Database.execute_query(create_attachments_table)
        print("✓ Created file_attachments table")

        Database.execute_query(create_indexes)
        print("✓ Created indexes")

        print("\n✅ Database migration completed successfully!")
        print("\nNew features available:")
        print("- Study Goals: Set and track study targets")
        print("- Study Streaks: Track consecutive study days")
        print("- Notifications: In-app notifications and reminders")
        print("- File Attachments: Attach files to tasks")

    except Exception as e:
        print(f"❌ Migration failed: {e}")
        return False

    return True

if __name__ == "__main__":
    success = run_migration()
    sys.exit(0 if success else 1)