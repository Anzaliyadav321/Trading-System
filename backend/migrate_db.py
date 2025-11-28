"""
Database migration script for adding missing columns
Run this once on Render to fix the schema
"""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.database import engine
from sqlalchemy import text

def migrate():
    print("Starting database migration...")
    
    with engine.connect() as conn:
        # Add is_active column
        try:
            conn.execute(text('ALTER TABLE users ADD COLUMN is_active BOOLEAN DEFAULT TRUE'))
            print("✓ Added is_active column")
        except Exception as e:
            if "already exists" in str(e).lower() or "duplicate" in str(e).lower():
                print("- is_active column already exists")
            else:
                print(f"! Error adding is_active: {e}")
        
        # Add is_superuser column
        try:
            conn.execute(text('ALTER TABLE users ADD COLUMN is_superuser BOOLEAN DEFAULT FALSE'))
            print("✓ Added is_superuser column")
        except Exception as e:
            if "already exists" in str(e).lower() or "duplicate" in str(e).lower():
                print("- is_superuser column already exists")
            else:
                print(f"! Error adding is_superuser: {e}")
        
        # Add role column
        try:
            conn.execute(text("ALTER TABLE users ADD COLUMN role VARCHAR(50) DEFAULT 'user'"))
            print("✓ Added role column")
        except Exception as e:
            if "already exists" in str(e).lower() or "duplicate" in str(e).lower():
                print("- role column already exists")
            else:
                print(f"! Error adding role: {e}")
        
        conn.commit()
    
    print("\nMigration complete!")

if __name__ == "__main__":
    migrate()