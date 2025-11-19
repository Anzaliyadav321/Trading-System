# backend/check_db.py
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("\n" + "="*80)
print("DATABASE SETUP & VERIFICATION SCRIPT")
print("="*80)

# Import database engine and base
from backend.core.database import Base, engine

print("\nImporting all models...")

# Import ALL models (this is critical)
from backend.core.auth.models import (
    User,
    Order,
    OrderType,
    StopLossPosition,
    StopLossStatus,
    UserPortfolio,
    Position,
    DailyEntry,
    PositionStatus
)

print("Models imported successfully")

# Check what tables SQLAlchemy knows about
print(f"\nModels registered with SQLAlchemy:")
for table_name in Base.metadata.tables.keys():
    print(f"   - {table_name}")

print("\nCreating tables...")

try:
    # Drop all tables first (clean slate)
    Base.metadata.drop_all(bind=engine)
    print("Dropped existing tables")
    
    # Create all tables
    Base.metadata.create_all(bind=engine)
    print("Created all tables")
    
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Verify tables were created
print("\n Verifying tables in database...")
from sqlalchemy import inspect

inspector = inspect(engine)
tables = inspector.get_table_names()

print(f"\n Tables found: {len(tables)}")
for table in tables:
    print(f"  {table}")

# Check new tables specifically
new_tables = ['user_portfolios', 'positions', 'daily_entries']
print("\n" + "="*80)
print("STOP LOSS TABLES CHECK")
print("="*80)

all_found = True
for table in new_tables:
    if table in tables:
        columns = inspector.get_columns(table)
        print(f"\n {table}: {len(columns)} columns")
        
        # Show first 5 columns
        print(f"   Columns:")
        for col in columns[:5]:
            print(f"   - {col['name']}: {col['type']}")
        if len(columns) > 5:
            print(f"   ... and {len(columns) - 5} more columns")
    else:
        print(f"\n {table}: NOT FOUND")
        all_found = False

print("\n" + "="*80)
if all_found:
    print("SUCCESS - All stop loss tables created!")
    print("   Your database is ready for the stop loss system!")
else:
    print("FAILED - Some tables missing")
    print("   Please check your models.py file")
print("="*80 + "\n")