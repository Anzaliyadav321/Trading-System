# backend/core/config.py
from pydantic_settings import BaseSettings
from dotenv import load_dotenv
import os

# Explicitly load .env file from backend/
BASE_DIR = os.path.dirname(os.path.dirname(__file__))  # backend/core → backend/
load_dotenv(dotenv_path=os.path.join(BASE_DIR, ".env"))

class Settings(BaseSettings):
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./trading.db")

    SECRET_KEY: str = os.getenv("SECRET_KEY", "your_super_secret_key_here")

    MAIL_USERNAME: str = os.getenv("MAIL_USERNAME", "")
    MAIL_PASSWORD: str = os.getenv("MAIL_PASSWORD", "")
    MAIL_FROM: str = os.getenv("MAIL_FROM", "")
    MAIL_PORT: int = int(os.getenv("MAIL_PORT", 587))
    MAIL_SERVER: str = os.getenv("MAIL_SERVER", "smtp.gmail.com")

settings = Settings()

# Debug check (optional)
print(f"MAIL_FROM loaded as: {settings.MAIL_FROM}")
