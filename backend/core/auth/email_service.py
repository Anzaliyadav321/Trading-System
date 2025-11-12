#backend/core/auth/email_service.py
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig
from backend.core.config import settings  # Import your app settings

# Configure FastMail using environment variables or settings
conf = ConnectionConfig(
    MAIL_USERNAME=settings.MAIL_USERNAME,
    MAIL_PASSWORD=settings.MAIL_PASSWORD,
    MAIL_FROM=settings.MAIL_FROM,
    MAIL_PORT=settings.MAIL_PORT,
    MAIL_SERVER=settings.MAIL_SERVER,
    MAIL_STARTTLS=True,
    MAIL_SSL_TLS=False,
    USE_CREDENTIALS=True,
)

# -------------------------------
# Send OTP Verification Email
# -------------------------------
async def send_verification_email(email: str, otp: str):
    """
    Sends an OTP email for user verification.
    """
    message = MessageSchema(
        subject="Your Trading App Verification OTP",
        recipients=[email],
        body=f"""
        Welcome to the Trading App!

        Your One-Time Password (OTP) for verifying your account is: {otp}

        This OTP will expire in 10 minutes.
        Please do not share it with anyone.

        Thank you,
        Trading App Team
        """,
        subtype="plain"
    )
    fm = FastMail(conf)
    await fm.send_message(message)
