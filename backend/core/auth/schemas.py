#backcens/core/auth/schemas.py
from pydantic import BaseModel, EmailStr, Field
from datetime import datetime
from typing import Optional, List
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

# backend/core/auth/schemas.py (ADD at the end)

from typing import Optional, List
from datetime import date

# Transaction Item Schemas
class TransactionItemBase(BaseModel):
    company_name: str
    symbol: str
    quantity: int
    rate: float
    amount: float
    commission_rate: Optional[float] = 0.0
    commission_amount: Optional[float] = 0.0
    nt_amount: Optional[float] = 0.0
    sebn_commission: Optional[float] = 0.0
    eff_rate: Optional[float] = 0.0
    total: Optional[float] = 0.0

class TransactionItemCreate(TransactionItemBase):
    pass

class TransactionItemResponse(TransactionItemBase):
    id: int
    transaction_id: int
    created_at: datetime
    
    class Config:
        from_attributes = True


# # backend/core/auth/schemas.py - Update TransactionCreate and TransactionResponse for bill

class TransactionCreate(BaseModel):
    """Schema for creating a new transaction (BUY or SELL)"""
    
    # Core fields
    symbol: str
    transaction_type: str = Field(..., pattern="^(BUY|SELL)$")
    quantity: int = Field(..., gt=0)
    price: float = Field(..., gt=0)
    stop_loss_price: Optional[float] = None
    notes: Optional[str] = None
    
    # BUY FIELDS
    bill_number: Optional[str] = None
    bill_date: Optional[date] = None
    sub_total: Optional[float] = 0.0
    grand_total: Optional[float] = 0.0
    share_amount: Optional[float] = 0.0
    share_quantity: Optional[int] = 0
    sebn_commission: Optional[float] = 0.0
    nepse_commission: Optional[float] = 0.0
    sebon_regulatory_fee: Optional[float] = 0.0
    broker_commission: Optional[float] = 0.0
    name_transfer_amount: Optional[float] = 0.0
    dp_amount: Optional[float] = 0.0
    total_commission: Optional[float] = 0.0
    clearance_date: Optional[date] = None
    net_receivable_amount: Optional[float] = 0.0
    
    # SELL FIELDS (NEW)
    sell_bill_number: Optional[str] = None
    sell_bill_date: Optional[date] = None
    base_price: Optional[float] = 0.0
    cgt: Optional[float] = 0.0
    capital_gain: Optional[float] = 0.0
    sebo_commission: Optional[float] = 0.0
    eff_rate: Optional[float] = 0.0
    payout: Optional[str] = 'No'
    co_qty: Optional[float] = 0.0
    co_amt: Optional[float] = 0.0
    net_payable_less_closeout: Optional[float] = 0.0
    
    # Common
    broker_name: Optional[str] = None
    broker_number: Optional[str] = None
    items: Optional[List[TransactionItemCreate]] = []


class TransactionResponse(BaseModel):
    """Response schema with all fields"""
    id: int
    user_id: int
    symbol: str
    transaction_type: str
    quantity: int
    price: float
    total_amount: float
    stop_loss_price: Optional[float] = None
    notes: Optional[str] = None
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    # BUY FIELDS
    bill_number: Optional[str] = None
    bill_date: Optional[date] = None
    sub_total: Optional[float] = 0.0
    grand_total: Optional[float] = 0.0
    share_amount: Optional[float] = 0.0
    share_quantity: Optional[int] = 0
    sebn_commission: Optional[float] = 0.0
    nepse_commission: Optional[float] = 0.0
    sebon_regulatory_fee: Optional[float] = 0.0
    broker_commission: Optional[float] = 0.0
    name_transfer_amount: Optional[float] = 0.0
    dp_amount: Optional[float] = 0.0
    total_commission: Optional[float] = 0.0
    clearance_date: Optional[date] = None
    net_receivable_amount: Optional[float] = 0.0
    
    # SELL FIELDS (NEW)
    sell_bill_number: Optional[str] = None
    sell_bill_date: Optional[date] = None
    base_price: Optional[float] = 0.0
    cgt: Optional[float] = 0.0
    capital_gain: Optional[float] = 0.0
    sebo_commission: Optional[float] = 0.0
    eff_rate: Optional[float] = 0.0
    payout: Optional[str] = 'No'
    co_qty: Optional[float] = 0.0
    co_amt: Optional[float] = 0.0
    net_payable_less_closeout: Optional[float] = 0.0
    
    # Common
    broker_name: Optional[str] = None
    broker_number: Optional[str] = None
    items: List[TransactionItemResponse] = []
    
    class Config:
        from_attributes = True