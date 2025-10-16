#backcens/core/auth/schemas.py
from pydantic import BaseModel, EmailStr
from datetime import datetime
from enum import Enum

class UserCreate(BaseModel):
    email: EmailStr
    password: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserOut(BaseModel):
    id: int
    email: EmailStr
    is_verified: bool

    class Config:
        from_attributes = True

# -------------------- ENUMS --------------------
class StopLossStatus(str, Enum):
    ACTIVE = "ACTIVE"
    TRIGGERED = "TRIGGERED"
    PARTIALLY_SOLD = "PARTIALLY_SOLD"
    FULLY_SOLD = "FULLY_SOLD"
    CLOSED = "CLOSED"

# -------------------- STOP LOSS SCHEMAS --------------------
class StopLossBase(BaseModel):
    symbol: str
    quantity: int
    entry_price: float  
    stop_loss_price: float  
    avg_price: float | None = None

class StopLossCreate(StopLossBase):
    pass

class StopLossOut(StopLossBase):
    id: int
    status: StopLossStatus
    user_email: str
    remaining_quantity: int
    quantity_sold: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True