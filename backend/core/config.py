# backend/core/config.py

from pydantic_settings import BaseSettings
from dotenv import load_dotenv
import os

# Force load .env from the backend/ folder
BASE_DIR = os.path.dirname(os.path.dirname(__file__))  # backend/core → backend/
ENV_PATH = os.path.join(BASE_DIR, ".env")
load_dotenv(ENV_PATH)

print(f"Loaded .env from: {ENV_PATH}")

class Settings(BaseSettings):
    DATABASE_URL: str
    SECRET_KEY: str
    BREVO_API_KEY: str
    BREVO_SENDER_EMAIL: str
    BREVO_SENDER_NAME: str
    ALGORITHM: str = "HS256"

    class Config:
        env_file = ENV_PATH
        env_file_encoding = 'utf-8'

settings = Settings()

print("BREVO API key:", settings.BREVO_API_KEY)
print("MAIL FROM:", settings.BREVO_SENDER_EMAIL)
print("MAIL FROM NAME:", settings.BREVO_SENDER_NAME)
