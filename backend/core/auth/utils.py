# backend/core/auth/utils.py

from fastapi import HTTPException
from backend.core.auth.email_service import send_verification_email

async def send_verification_link(email: str, token: str):
    try:
        await send_verification_email(email, token)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error sending email: {e}")
