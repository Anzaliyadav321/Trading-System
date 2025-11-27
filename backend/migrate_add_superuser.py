"""
Migration script to add is_superuser, is_active, and role fields to User table
"""
import sys
from pathlib import Path

# Add backend directory to path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from sqlalchemy import text
from core.database import engine

def migrate():
    print("🔄 Starting migration...")
    print("=" * 60)
    
    with engine.connect() as conn:
        # Check current schema
        result = conn.execute(text("PRAGMA table_info(users)"))
        columns = {row[1] for row in result}
        
        print("Current columns in users table:")
        for col in columns:
            print(f"  - {col}")
        print()
        
        # Add is_superuser if missing
        if 'is_superuser' not in columns:
            print("Adding is_superuser column...")
            conn.execute(text("""
                ALTER TABLE users 
                ADD COLUMN is_superuser BOOLEAN DEFAULT 0
            """))
            conn.commit()
            print("✅ Added is_superuser column")
        else:
            print("✓ is_superuser column already exists")
        
        # Add is_active if missing
        if 'is_active' not in columns:
            print("Adding is_active column...")
            conn.execute(text("""
                ALTER TABLE users 
                ADD COLUMN is_active BOOLEAN DEFAULT 1
            """))
            conn.commit()
            print("✅ Added is_active column")
        else:
            print("✓ is_active column already exists")
        
        # Add role if missing
        if 'role' not in columns:
            print("Adding role column...")
            conn.execute(text("""
                ALTER TABLE users 
                ADD COLUMN role VARCHAR DEFAULT 'user'
            """))
            conn.commit()
            print("✅ Added role column")
        else:
            print("✓ role column already exists")
        
        print()
        print("=" * 60)
        print("Migration completed successfully!")
        print("=" * 60)

if __name__ == "__main__":
    try:
        migrate()
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        import traceback
        traceback.print_exc()