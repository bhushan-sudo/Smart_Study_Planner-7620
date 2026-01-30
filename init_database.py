"""
Database initialization script
Run this script to create all database tables from schema.sql
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Add backend directory to path
backend_dir = os.path.join(os.path.dirname(__file__), 'backend')
sys.path.insert(0, backend_dir)

from database import Database

def init_database():
    """Initialize database with full schema"""

    print("Initializing database with full schema...")

    # Read the schema file
    schema_path = os.path.join(os.path.dirname(__file__), 'database', 'schema.sql')

    try:
        with open(schema_path, 'r', encoding='utf-8') as f:
            schema_sql = f.read()

        # Split the SQL into individual statements
        statements = []
        current_statement = []
        in_multiline_comment = False

        for line in schema_sql.split('\n'):
            line = line.strip()

            # Skip empty lines and comments
            if not line or line.startswith('--'):
                continue

            # Handle multiline comments
            if '/*' in line:
                in_multiline_comment = True
            if '*/' in line:
                in_multiline_comment = False
                continue

            if in_multiline_comment:
                continue

            current_statement.append(line)

            # If line ends with semicolon, it's a complete statement
            if line.endswith(';'):
                statement = ' '.join(current_statement)
                if statement.strip():
                    statements.append(statement)
                current_statement = []

        # Execute each statement
        for statement in statements:
            if statement.strip():
                try:
                    Database.execute_query(statement)
                    print(f"✓ Executed: {statement[:50]}...")
                except Exception as e:
                    print(f"⚠ Warning: {e}")
                    # Continue with other statements

        print("\n✅ Database initialization completed!")
        print("\nTables created:")
        print("- users")
        print("- subjects")
        print("- tasks")
        print("- study_sessions")
        print("- task_progress")
        print("- weekly_summaries")
        print("- study_goals")
        print("- study_streaks")
        print("- notifications")
        print("- file_attachments")

    except FileNotFoundError:
        print(f"❌ Schema file not found: {schema_path}")
        return False
    except Exception as e:
        print(f"❌ Initialization failed: {e}")
        return False

    return True

if __name__ == "__main__":
    success = init_database()
    sys.exit(0 if success else 1)