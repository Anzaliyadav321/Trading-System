#backcend/core/auth/models.py

from sqlalchemy import Column, Integer, String, Boolean, Float, DateTime, ForeignKey, Enum
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
from backend.core.database import Base



# -------------------- ENUMS --------------------
class OrderType(enum.Enum):
    BUY = "BUY"
    SELL = "SELL"

class StopLossStatus(enum.Enum):
    ACTIVE = "ACTIVE"
    TRIGGERED = "TRIGGERED"
    PARTIALLY_SOLD = "PARTIALLY_SOLD"
    FULLY_SOLD = "FULLY_SOLD"

# -------------------- MODELS --------------------
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_verified = Column(Boolean, default=False)
    otp = Column(String, nullable=True)
    otp_created_at = Column(DateTime, default=datetime.utcnow, nullable=True)

    orders = relationship("Order", back_populates="user")


class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    user_email = Column(String, ForeignKey("users.email"), nullable=False)
    symbol = Column(String, nullable=False, index=True)
    quantity = Column(Integer, nullable=False)
    price = Column(Float, nullable=False)
    amount = Column(Float, nullable=False)
    order_type = Column(Enum(OrderType), nullable=False)
    status = Column(String, default="PENDING")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="orders")


class StopLossPosition(Base):
    __tablename__ = "stop_loss_positions"

    id = Column(Integer, primary_key=True, index=True)
    user_email = Column(String, ForeignKey("users.email"), nullable=False)
    symbol = Column(String, nullable=False)
    buy_price = Column(Float, nullable=False)
    stoploss = Column(Float, nullable=False)
    avg_price = Column(Float, nullable=True)  
    quantity = Column(Integer, nullable=False)
    remaining_qty = Column(Integer, nullable=False)
    status = Column(Enum(StopLossStatus), default=StopLossStatus.ACTIVE)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
