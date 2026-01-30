"""
Database Initialization Script for SQLite
Creates and initializes the SQLite database for the Study Planner app
"""

import sqlite3
import os
from datetime import datetime

def initialize_sqlite_db():
    """Initialize SQLite database with schema"""

    db_path = os.path.join(os.path.dirname(__file__), 'study_planner.db')

    # Remove existing database if it exists
    if os.path.exists(db_path):
        print(f"Removing existing database: {db_path}")
        os.remove(db_path)

    print(f"Creating new SQLite database: {db_path}")

    # Connect to database
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON")

    try:
        # Read and execute schema
        schema_path = os.path.join(os.path.dirname(__file__), 'database', 'schema_sqlite.sql')
        with open(schema_path, 'r', encoding='utf-8') as f:
            schema_sql = f.read()

        # Split into individual statements and execute
        statements = []
        current_statement = []
        in_string = False
        string_char = None

        for char in schema_sql:
            if not in_string and char in ('"', "'"):
                in_string = True
                string_char = char
            elif in_string and char == string_char and current_statement and current_statement[-1] != '\\':
                in_string = False
                string_char = None

            current_statement.append(char)

            if not in_string and char == ';':
                statement = ''.join(current_statement).strip()
                if statement and not statement.startswith('--'):
                    statements.append(statement)
                current_statement = []

        # Execute statements
        for statement in statements:
            if statement.strip():
                try:
                    conn.execute(statement)
                except Exception as e:
                    print(f"Error executing statement: {statement[:100]}...")
                    print(f"Error: {e}")
                    raise

        conn.commit()
        print("Database schema created successfully!")

        # Create uploads directory
        uploads_dir = os.path.join(os.path.dirname(__file__), 'uploads')
        os.makedirs(uploads_dir, exist_ok=True)
        print(f"Uploads directory created: {uploads_dir}")

        # Insert some sample data for testing
        print("Inserting sample data...")

        # Sample user
        conn.execute("""
            INSERT INTO users (username, email, password_hash, full_name)
            VALUES (?, ?, ?, ?)
        """, ('testuser', 'test@example.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/Le0KdV0K1Z9K9K9K', 'Test User'))

        # Sample subjects
        subjects = [
            ('Mathematics', '#3B82F6'),
            ('Physics', '#EF4444'),
            ('Chemistry', '#10B981'),
            ('Biology', '#F59E0B'),
            ('English', '#8B5CF6')
        ]

        for subject_name, color in subjects:
            conn.execute("""
                INSERT INTO subjects (user_id, subject_name, color_code)
                VALUES (?, ?, ?)
            """, (1, subject_name, color))

        # Sample tasks
        tasks = [
            ('Complete Calculus homework', 'Chapter 5 exercises', 1, 3, 2.0, '2026-01-30', 'pending'),
            ('Physics lab report', 'Write up experiment results', 2, 4, 3.0, '2026-01-28', 'in_progress'),
            ('Chemistry quiz preparation', 'Review organic chemistry', 3, 2, 1.5, '2026-01-27', 'pending'),
            ('Biology reading', 'Chapter 12 - Cell division', 4, 3, 2.0, '2026-01-29', 'completed'),
            ('English essay', 'Write 1000-word essay on Shakespeare', 5, 4, 4.0, '2026-02-01', 'pending')
        ]

        for title, desc, subject_id, priority, hours, deadline, status in tasks:
            conn.execute("""
                INSERT INTO tasks (user_id, subject_id, title, description, priority, estimated_hours, deadline, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (1, subject_id, title, desc, priority, hours, deadline, status))

        conn.commit()
        print("Sample data inserted successfully!")

        conn.close()
        print("Database initialization completed successfully!")
        return True

    except Exception as e:
        conn.close()
        print(f"Database initialization failed: {e}")
        return False

if __name__ == "__main__":
    print("SQLite Database Initialization Script")
    print("=" * 50)
    print(f"Started at: {datetime.now()}")

    success = initialize_sqlite_db()

    if success:
        print("\n✅ Database initialized successfully!")
        print("You can now run the Flask backend with SQLite.")
    else:
        print("\n❌ Database initialization failed!")
        exit(1)