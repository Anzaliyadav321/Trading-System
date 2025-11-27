# backend/core/database.py
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os

# Get DATABASE_URL from environment variable (set by Render)
DATABASE_URL = os.getenv("DATABASE_URL")

# Fallback to SQLite for local development
if not DATABASE_URL:
    print("[WARNING] DATABASE_URL not found in environment. Using SQLite for local development.")
    DATABASE_URL = "sqlite:///./trading.db"
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False}  # SQLite specific
    )
else:
    # Fix for Render PostgreSQL URLs (they use postgres:// instead of postgresql://)
    if DATABASE_URL.startswith("postgres://"):
        DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)
    
    print(f"[INFO] Connecting to PostgreSQL database...")
    
    # PostgreSQL connection (no check_same_thread needed)
    engine = create_engine(
        DATABASE_URL,
        pool_pre_ping=True,      # Verify connections before using
        pool_recycle=3600,       # Recycle connections every hour
        pool_size=5,             # Connection pool size
        max_overflow=10,         # Max overflow connections
        echo=False               # Set to True for SQL query logging
    )

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for all models
Base = declarative_base()

def get_db():
    """Dependency for FastAPI to get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# -----------------------------------------------------
# IMPORT ALL MODELS HERE
# -----------------------------------------------------
# This ensures SQLAlchemy detects the tables and creates them
from core.auth import models


# -----------------------------------------------------
# CREATE ALL DATABASE TABLES
# -----------------------------------------------------
def init_db():
    """Initialize database - create all tables"""
    try:
        print("\n" + "="*80)
        print("INITIALIZING DATABASE...")
        print("="*80)
        
        Base.metadata.create_all(bind=engine)
        
        print("\nDatabase tables created successfully!")
        print(f"Tables in database: {len(Base.metadata.tables)}")
        for table_name in Base.metadata.tables.keys():
            print(f"   {table_name}")
        print("="*80 + "\n")
        
    except Exception as e:
        print(f"\n[ERROR] Failed to initialize database: {e}")
        import traceback
        traceback.print_exc()
        raise

# Auto-create tables on import (for development)
# Comment this out if using Alembic migrations
Base.metadata.create_all(bind=engine)