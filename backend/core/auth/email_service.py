# #backend/core/auth/email_service.py
# from fastapi_mail import FastMail, MessageSchema, ConnectionConfig
# from backend.core.config import settings  # Import your app settings

# # Configure FastMail using environment variables or settings
# conf = ConnectionConfig(
#     MAIL_USERNAME=settings.MAIL_USERNAME,
#     MAIL_PASSWORD=settings.MAIL_PASSWORD,
#     MAIL_FROM=settings.MAIL_FROM,
#     # MAIL_PORT=settings.MAIL_PORT,
#     MAIL_PORT = 587,
#     MAIL_SERVER="smtp-relay.brevo.com",
#     MAIL_STARTTLS=True,
#     MAIL_SSL_TLS=False,
#     USE_CREDENTIALS=True,
#     VALIDATE_CERTS=True

# )

# # -------------------------------
# # Send OTP Verification Email
# # -------------------------------
# async def send_verification_email(email: str, otp: str):
#     """
#     Sends an OTP email for user verification.
#     """
#     message = MessageSchema(
#         subject="Your Trading App Verification OTP",
#         recipients=[email],
#         body=f"""
#         Welcome to the Trading App!

#         Your One-Time Password (OTP) for verifying your account is: {otp}

#         This OTP will expire in 10 minutes.
#         Please do not share it with anyone.

#         Thank you,
#         Trading App Team
#         """,
#         subtype="plain"
#     )
#     fm = FastMail(conf)
#     await fm.send_message(message)


# for using brevo api instead of smtp
# backend/core/auth/email_service.py

# backend/core/auth/email_service.py

import httpx
from fastapi import HTTPException
from backend.core.config import settings

BREVO_API_KEY = settings.BREVO_API_KEY
BREVO_SENDER_EMAIL = settings.BREVO_SENDER_EMAIL
BREVO_SENDER_NAME = settings.BREVO_SENDER_NAME


BREVO_API_URL = "https://api.brevo.com/v3/smtp/email"


async def send_verification_email(recipient_email: str, otp: str):
    """
    Send a verification email with OTP using Brevo's API.
    """
    if not BREVO_API_KEY:
        raise HTTPException(status_code=500, detail="Brevo API key not configured")

    subject = "Your OTP Verification Code"
    html_content = f"""
    <html>
        <body>
            <p>Hello,</p>
            <p>Your OTP code for verification is: <strong>{otp}</strong></p>
            <p>This code will expire in 10 minutes.</p>
            <p>Thank you,<br>{BREVO_SENDER_NAME}</p>
        </body>
    </html>
    """

    data = {
        "sender": {"name": BREVO_SENDER_NAME, "email": BREVO_SENDER_EMAIL},
        "to": [{"email": recipient_email}],
        "subject": subject,
        "htmlContent": html_content
    }

    headers = {
        "accept": "application/json",
        "api-key": BREVO_API_KEY,
        "content-type": "application/json"
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(BREVO_API_URL, headers=headers, json=data)

    if response.status_code != 201:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to send email: {response.text}"
        )

    return {"message": "Verification email sent successfully"}
