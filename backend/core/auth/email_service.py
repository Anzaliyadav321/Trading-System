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

import os
import requests

# Get environment variables
BREVO_API_KEY = os.getenv("BREVO_API_KEY")
MAIL_FROM = os.getenv("MAIL_FROM", "trade8561@gmail.com")
MAIL_FROM_NAME = os.getenv("MAIL_FROM_NAME", "Trading System")

def send_verification_email(email: str, otp: str):
    """
    Sends an OTP verification email using Brevo API (no SMTP).
    """

    url = "https://api.brevo.com/v3/smtp/email"

    headers = {
        "accept": "application/json",
        "api-key": BREVO_API_KEY,
        "content-type": "application/json",
    }

    payload = {
        "sender": {"name": MAIL_FROM_NAME, "email": MAIL_FROM},
        "to": [{"email": email}],
        "subject": "Your Trading System Verification OTP",
        "htmlContent": f"""
            <p>Welcome to <b>Trading System</b>!</p>
            <p>Your One-Time Password (OTP) is: <b>{otp}</b></p>
            <p>This OTP will expire in 10 minutes. Please do not share it.</p>
            <p>Thank you,<br>Trading System Team</p>
        """
    }

    response = requests.post(url, headers=headers, json=payload)

    if response.status_code != 201:
        raise Exception(f"Email sending failed: {response.text}")

    return response.json()

