#backend/core/auth/routes.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import random
from jose import JWTError, jwt

from backend.core.database import get_db
from backend.core.auth import models, schemas, email_service
from backend.core.security import (
    hash_password,
    verify_password,
    create_access_token,
    SECRET_KEY,
    ALGORITHM,
)

router = APIRouter(prefix="/auth", tags=["Authentication"])


# ---------------------------
# REGISTER (SEND OTP)
# ---------------------------
@router.post("/register")
async def register_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    existing = db.query(models.User).filter(models.User.email == user.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    hashed_pw = hash_password(user.password)
    otp = str(random.randint(100000, 999999))  # 6-digit OTP

    new_user = models.User(
        email=user.email,
        hashed_password=hashed_pw,
        otp=otp,
        otp_created_at=datetime.utcnow(),
        is_verified=False,
    )
    db.add(new_user)
    db.commit()

    # Send OTP to email
    await email_service.send_verification_email(user.email, otp)
    return {"message": "OTP sent to your email for verification."}


# ---------------------------
# VERIFY OTP
# ---------------------------
@router.post("/verify-otp")
def verify_otp(email: str, otp: str, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if user.is_verified:
        return {"message": "User already verified."}

    # Check OTP validity
    if user.otp != otp:
        raise HTTPException(status_code=400, detail="Invalid OTP")

    # Check OTP expiration (10 min)
    if (datetime.utcnow() - user.otp_created_at) > timedelta(minutes=10):
        raise HTTPException(status_code=400, detail="OTP expired. Please request a new one.")

    # Mark as verified
    user.is_verified = True
    user.otp = None
    user.otp_created_at = None
    db.commit()

    return {"message": "Email verified successfully! You can now log in."}


# ---------------------------
# RESEND OTP
# ---------------------------
@router.post("/resend-otp")
async def resend_otp(email: str, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if user.is_verified:
        return {"message": "User already verified. You can log in directly."}

    otp = str(random.randint(100000, 999999))
    user.otp = otp
    user.otp_created_at = datetime.utcnow()
    db.commit()

    await email_service.send_verification_email(email, otp)
    return {"message": "New OTP sent to your email."}


# ---------------------------
# LOGIN
# ---------------------------
@router.post("/login")
def login(user: schemas.UserLogin, db: Session = Depends(get_db)):
    db_user = db.query(models.User).filter(models.User.email == user.email).first()
    if not db_user or not verify_password(user.password, db_user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    if not db_user.is_verified:
        raise HTTPException(status_code=403, detail="Please verify your email using OTP before login")

    token = create_access_token({"sub": db_user.email, "is_superuser": db_user.is_superuser})
    return {"access_token": token, "token_type": "bearer"}


# ---------------------------
# GET CURRENT USER (OPTIONAL)
# ---------------------------
from fastapi.security import OAuth2PasswordBearer
from fastapi import Security

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

@router.get("/me")
def get_current_user(token: str = Security(oauth2_scheme), db: Session = Depends(get_db)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email = payload.get("sub")
        if email is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        user = db.query(models.User).filter(models.User.email == email).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        return {"email": user.email, "is_verified": user.is_verified}
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
