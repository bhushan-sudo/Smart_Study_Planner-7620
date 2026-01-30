
import sys
import os

# Add current directory to path to allow imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import Database

def migrate():
    try:
        print("Starting migration...")
        
        # Add new columns if they don't exist
        columns = [
            ("level", "VARCHAR(50)"),
            ("target_grade", "VARCHAR(50)"),
            ("current_topic", "VARCHAR(255)"),
            ("sub_topics", "TEXT")
        ]

        for col_name, col_type in columns:
            query = f"ALTER TABLE subjects ADD COLUMN IF NOT EXISTS {col_name} {col_type};"
            try:
                Database.execute_query(query, fetch=False)
                print(f"Added column {col_name}")
            except Exception as e:
                print(f"Error adding column {col_name}: {e}")

        print("Migration completed successfully.")

    except Exception as e:
        print(f"Migration failed: {e}")

if __name__ == "__main__":
    migrate()
