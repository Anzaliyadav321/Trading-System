# backend/core/auth/models.py

from sqlalchemy import Column, Integer, String, Boolean, Float, DateTime, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
from backend.core.database import Base


# ============================================
# ENUMS
# ============================================

class OrderType(enum.Enum):
    """Order type enum"""
    BUY = "BUY"
    SELL = "SELL"


class StopLossStatus(enum.Enum):
    """Stop loss position status (legacy - for backward compatibility)"""
    ACTIVE = "ACTIVE"
    TRIGGERED = "TRIGGERED"
    PARTIALLY_SOLD = "PARTIALLY_SOLD"
    FULLY_SOLD = "FULLY_SOLD"


class PositionStatus(str, enum.Enum):
    """Position status enum (new system)"""
    ACTIVE = "ACTIVE"
    CLOSED = "CLOSED"




class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_verified = Column(Boolean, default=False)
    otp = Column(String, nullable=True)
    otp_created_at = Column(DateTime, default=datetime.utcnow, nullable=True)

    # Relationships
    orders = relationship("Order", back_populates="user")
    portfolio = relationship("UserPortfolio", back_populates="user", uselist=False)  # NEW


class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    user_email = Column(String, ForeignKey("users.email"), nullable=False)
    symbol = Column(String, nullable=False, index=True)
    quantity = Column(Integer, nullable=False)
    price = Column(Float, nullable=False)
    amount = Column(Float, nullable=False)
    order_type = Column(SQLEnum(OrderType), nullable=False)
    status = Column(String, default="PENDING")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationship
    user = relationship("User", back_populates="orders")


class StopLossPosition(Base):
    """Legacy stop loss tracking - kept for backward compatibility"""
    __tablename__ = "stop_loss_positions"

    id = Column(Integer, primary_key=True, index=True)
    user_email = Column(String, ForeignKey("users.email"), nullable=False)
    symbol = Column(String, nullable=False)
    buy_price = Column(Float, nullable=False)
    stoploss = Column(Float, nullable=False)
    avg_price = Column(Float, nullable=True)
    quantity = Column(Integer, nullable=False)
    remaining_qty = Column(Integer, nullable=False)
    status = Column(SQLEnum(StopLossStatus), default=StopLossStatus.ACTIVE)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


# ============================================
# NEW MODELS FOR REAL TRADING SYSTEM
# ============================================

class UserPortfolio(Base):
    """
    User's portfolio - tracks capital and cash balance
    Each user has ONE portfolio with ₹10 lakh default capital
    """
    __tablename__ = "user_portfolios"

    id = Column(Integer, primary_key=True, index=True)
    user_email = Column(String, ForeignKey("users.email"), unique=True, nullable=False)

    # Capital tracking
    total_capital = Column(Float, default=1000000.0)  # ₹10 lakh default
    available_cash = Column(Float, default=1000000.0)  # Current available cash
    invested_amount = Column(Float, default=0.0)  # Money currently in positions

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="portfolio")
    positions = relationship("Position", back_populates="portfolio", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<UserPortfolio(email={self.user_email}, capital={self.total_capital})>"


class Position(Base):
    """
    Trading position - implements TradingSystem logic
    Tracks a stock position from Day 1 to exit (up to 90 days)
    """
    __tablename__ = "positions"

    id = Column(Integer, primary_key=True, index=True)
    user_email = Column(String, ForeignKey("users.email"), nullable=False, index=True)
    portfolio_id = Column(Integer, ForeignKey("user_portfolios.id"), nullable=False)

    # Stock identification
    symbol = Column(String, nullable=False, index=True)

    # Entry information
    entry_day = Column(Integer, default=1)  # Day 1, 2, 3, or 4
    entry_price = Column(Float, nullable=False)  # First entry price (Day 1)
    total_quantity = Column(Float, nullable=False)  # Total shares bought
    total_invested = Column(Float, nullable=False)  # Total rupees invested

    # Price tracking
    avg_buy_price = Column(Float, nullable=False)  # Weighted average buy price
    current_price = Column(Float, nullable=False)  # Latest market price
    max_closing_price = Column(Float, default=0.0)  # Highest closing price (for Day 5+ SL)

    # Stop loss tracking (PO-approved logic)
    sl_price = Column(Float, default=0.0)  # Current stop loss price
    sl_level = Column(String, default="default")  # default/level_20/level_30/level_40
    highest_sl_level_achieved = Column(String, default="default")  # Cannot downgrade
    profit_40_achieved = Column(Boolean, default=False)  # Track if 40% profit hit

    # Time tracking
    days_held = Column(Integer, default=1)  # Number of days held
    can_add_more = Column(Boolean, default=True)  # False after Day 4 or SL hit during Days 2-4

    # Status
    status = Column(SQLEnum(PositionStatus), default=PositionStatus.ACTIVE)

    # Exit information (when closed)
    exit_price = Column(Float, nullable=True)
    exit_reason = Column(String, nullable=True)  # "SL Hit", "Manual", "90-day exit"
    exit_date = Column(DateTime, nullable=True)
    profit_loss = Column(Float, default=0.0)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    portfolio = relationship("UserPortfolio", back_populates="positions")
    daily_entries = relationship("DailyEntry", back_populates="position", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Position(symbol={self.symbol}, days={self.days_held}, status={self.status})>"


class DailyEntry(Base):
    """
    Daily entries for Days 1-4 (25% allocation each day)
    Tracks each individual buy entry for weighted average calculation
    """
    __tablename__ = "daily_entries"

    id = Column(Integer, primary_key=True, index=True)
    position_id = Column(Integer, ForeignKey("positions.id"), nullable=False)

    # Entry details
    day_number = Column(Integer, nullable=False)  # 1, 2, 3, or 4
    entry_price = Column(Float, nullable=False)  # Price at which bought
    quantity = Column(Float, nullable=False)  # Shares bought this day
    amount_invested = Column(Float, nullable=False)  # Rupees invested this day

    # Timestamp
    entry_date = Column(DateTime, default=datetime.utcnow)

    # Relationship
    position = relationship("Position", back_populates="daily_entries")

    def __repr__(self):
        return f"<DailyEntry(day={self.day_number}, price={self.entry_price}, qty={self.quantity})>"