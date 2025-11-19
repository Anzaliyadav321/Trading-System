#backend/core/database.py
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

DATABASE_URL = "sqlite:///./trading.db"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# -----------------------------------------------------
# IMPORT ALL MODELS HERE
# -----------------------------------------------------
# This ensures SQLAlchemy detects the tables and creates them
from backend.core.auth import models


# -----------------------------------------------------
# CREATE ALL DATABASE TABLES (no Alembic)
# -----------------------------------------------------
# Base.metadata.create_all(bind=engine)
