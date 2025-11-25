# backend/core/auth/dependencies.py
"""
Authentication dependencies for route protection
"""

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from sqlalchemy.orm import Session
from datetime import datetime, timezone
from backend.core.database import SessionLocal
from backend.core.auth.models import User
from backend.core.config import settings

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def get_db():
    """Database dependency"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_user_by_email(db: Session, email: str):
    """Helper to get user by email"""
    return db.query(User).filter(User.email == email).first()


# In dependencies.py, update get_current_user:

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    """
    Dependency to get current authenticated user from JWT token
    """
    try:
        # Debug logging
        current_time = datetime.now(timezone.utc)  # Use timezone-aware datetime
        print(f"[JWT DEBUG] Decoding token at {current_time}")
        print(f"[JWT DEBUG] Using SECRET_KEY: {settings.SECRET_KEY[:10]}...")
        
        # Decode without verification first to see the payload
        unverified_payload = jwt.decode(
            token, 
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],
            options={"verify_signature": False, "verify_exp": False}
        )
        print(f"[JWT DEBUG] Token payload: {unverified_payload}")
        
        if 'exp' in unverified_payload:
            # ✅ Use timezone-aware datetime
            exp_datetime = datetime.fromtimestamp(unverified_payload['exp'], tz=timezone.utc)
            print(f"[JWT DEBUG] Token expires (UTC): {exp_datetime}")
            print(f"[JWT DEBUG] Current time (UTC): {current_time}")
            time_diff = (exp_datetime - current_time).total_seconds()
            print(f"[JWT DEBUG] Time until expiry: {time_diff} seconds ({time_diff/60:.2f} minutes)")
        
        # Now decode with verification
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        email = payload.get("sub")
        
        if not email:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token: missing email"
            )
        
        # Get user from database
        user = get_user_by_email(db, email)
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        if not user.is_verified:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Email not verified"
            )
        
        print(f"[JWT DEBUG] Successfully authenticated user: {email}")
        return user
        
    except JWTError as e:
        print(f"[JWT ERROR] {type(e).__name__}: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid or expired token: {str(e)}"
        )    