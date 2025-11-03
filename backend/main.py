#backend/main.py
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from datetime import datetime, timedelta, date
from jose import jwt, JWTError
import bcrypt, random, os
import pandas as pd
from sqlalchemy.orm import Session
from sqlalchemy import func
from dotenv import load_dotenv

# Local imports
from backend.core.database import Base, engine, SessionLocal
from backend.core.auth.models import User, Order, OrderType, StopLossPosition, StopLossStatus
from backend.core.auth.schemas import StopLossCreate
from backend.core.auth import email_service
from backend.core.pipeline.nepse_pipeline import get_today_signals, run_pipeline
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime
import subprocess
import os

# Load environment variables
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), ".env"))

# App initialization
app = FastAPI(title="Trading System with JWT + OTP + DB Orders", version="1.0.0")

def run_merolagani_pipeline():
    script_path = os.path.join(os.getcwd(), "backend", "scripts", "merolagani_daily.py")
    print(f"[INFO] Running merolagani_daily at {datetime.now()}")
    subprocess.run(["python", script_path], check=True)

# Initialize scheduler
scheduler = BackgroundScheduler()
scheduler.add_job(run_merolagani_pipeline, "cron", hour=14, minute=15)  #  runs daily at 8:00 pm as render time is utc
scheduler.start()

@app.on_event("startup")
def startup_event():
    print("[INFO] Scheduler started — merolagani_daily will run every day at 8:00 PM Nepali time")

@app.on_event("shutdown")
def shutdown_event():
    scheduler.shutdown()

SECRET_KEY = os.getenv("SECRET_KEY", "your_super_secret_key_here")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60



# Allow CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://trading-system-anzis-projects-f933b6e6.vercel.app"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

# Cache for signals (to avoid recalculating on every request)
_signals_cache = None
_cache_timestamp = None

# Database utilities
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# JWT helpers
def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))

def get_user_by_email(db, email: str):
    return db.query(User).filter(User.email == email).first()

def get_current_user(token: str = Depends(oauth2_scheme), db=Depends(get_db)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email = payload.get("sub")
        if not email:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
        user = get_user_by_email(db, email)
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
        if not user.is_verified:
            raise HTTPException(status_code=403, detail="Email not verified")
        return user
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")

# Helper function to calculate recommended quantity
def calculate_recommended_quantity(signal):
    """Calculate recommended buy quantity based on price and volume"""
    try:
        price = float(signal.get("close", 0))
        if price == 0 or price < 10:
            return 0
        
        # Get previous day volume
        prev_volume = signal.get("Prev_Volume")
        if prev_volume and pd.notna(prev_volume):
            prev_vol_int = int(float(prev_volume))
            # Recommend up to 10% of previous day volume
            max_qty = int(prev_vol_int * 0.1)
            
            # Cap at reasonable amount (~Rs. 50,000 worth)
            max_amount = 50000
            qty_by_amount = int(max_amount / price)
            
            return min(max_qty, qty_by_amount, 500)  # Max 500 shares
        
        # Default: buy enough for ~Rs. 10,000 position
        return max(10, min(int(10000 / price), 200))
    except:
        return 100  # Default fallback

# Schemas
class RegisterRequest(BaseModel):
    email: str
    password: str

class VerifyOTPRequest(BaseModel):
    email: str
    otp: str

class OrderBooking(BaseModel):
    symbol: str
    quantity: int
    price: float
    order_type: str  # BUY or SELL

# Authentication Routes
@app.post("/auth/register")
async def register_user(request: RegisterRequest, db: Session = Depends(get_db)):
    existing_user = get_user_by_email(db, request.email)
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    hashed_pw = bcrypt.hashpw(request.password.encode("utf-8")[:72], bcrypt.gensalt())
    otp = str(random.randint(100000, 999999))

    new_user = User(
        email=request.email,
        hashed_password=hashed_pw.decode("utf-8"),
        otp=otp,
        otp_created_at=datetime.utcnow(),
        is_verified=False
    )
    db.add(new_user)
    db.commit()

    await email_service.send_verification_email(request.email, otp)
    return {"message": "User registered successfully. Please check your email for OTP."}

@app.post("/auth/verify-otp")
async def verify_otp(request: VerifyOTPRequest, db: Session = Depends(get_db)):
    user = get_user_by_email(db, request.email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if (datetime.utcnow() - user.otp_created_at).seconds > 300:
        raise HTTPException(status_code=400, detail="OTP expired")

    if user.otp != request.otp:
        raise HTTPException(status_code=400, detail="Invalid OTP")

    user.is_verified = True
    user.otp = None
    db.commit()
    return {"message": "Email verified successfully. You can now log in."}

@app.post("/auth/login")
async def login_user(form_data: OAuth2PasswordRequestForm = Depends(), db=Depends(get_db)):
    user = get_user_by_email(db, form_data.username)
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Invalid credentials")
    if not user.is_verified:
        raise HTTPException(status_code=403, detail="Email not verified")

    token_data = {"sub": user.email}
    access_token = create_access_token(data=token_data)
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/auth/me")
async def get_me(current_user: User = Depends(get_current_user)):
    return {"email": current_user.email, "verified": current_user.is_verified}

# Signal Routes (Using Real NEPSE Data)
@app.get("/signals/today")
async def get_today_signals_endpoint(current_user: User = Depends(get_current_user)):
    """Get today's trading signals from NEPSE pipeline"""
    global _signals_cache, _cache_timestamp
    
    try:
        # Use cache if available and less than 5 minutes old
        if _signals_cache and _cache_timestamp:
            if (datetime.utcnow() - _cache_timestamp).seconds < 300:
                return {
                    "success": True,
                    "signals": _signals_cache,
                    "timestamp": _cache_timestamp.isoformat(),
                    "count": len(_signals_cache),
                    "cached": True
                }
        
        # Get fresh signals from pipeline
        signals = get_today_signals()
        
        # Transform to frontend format
        formatted_signals = []
        for signal in signals:
            # Calculate change percentage if not present
            change_pct = 0
            if "change_percent" in signal:
                change_pct = float(signal["change_percent"])
            elif signal.get("close") and signal.get("open"):
                change_pct = ((float(signal["close"]) - float(signal["open"])) / float(signal["open"])) * 100
            
            # Get previous day volume for 10% sell rule
            prev_vol = signal.get("Prev_Volume")
            previous_day_volume = int(prev_vol) if prev_vol and pd.notna(prev_vol) else None
            
            formatted_signals.append({
                "symbol": signal.get("symbol", "N/A"),
                "price": float(signal.get("close", 0)),
                "change": round(change_pct, 2),
                "signal": signal.get("Recommendation", "HOLD"),
                "quantity": calculate_recommended_quantity(signal),
                "rsi": round(float(signal.get("RSI", 0)), 2) if signal.get("RSI") and pd.notna(signal.get("RSI")) else None,
                "ma50": round(float(signal.get("MA50", 0)), 2) if signal.get("MA50") and pd.notna(signal.get("MA50")) else None,
                "macd": round(float(signal.get("MACD", 0)), 4) if signal.get("MACD") and pd.notna(signal.get("MACD")) else None,
                "macd_signal": round(float(signal.get("MACD_Signal", 0)), 4) if signal.get("MACD_Signal") and pd.notna(signal.get("MACD_Signal")) else None,
                "volume": int(signal.get("volume", 0)) if signal.get("volume") else None,
                "prev_volume": previous_day_volume,
                "previousDayVolume": previous_day_volume,
                "date": str(signal.get("date")),
                "rsi_ok": bool(signal.get("RSI_OK", False)),
                "ma_ok": bool(signal.get("MA_OK", False)),
                "macd_ok": bool(signal.get("MACD_OK", False)),
                "volume_ok": bool(signal.get("VOLUME_OK", False))
            })
        
        # Update cache
        _signals_cache = formatted_signals
        _cache_timestamp = datetime.utcnow()
        
        return {
            "success": True,
            "signals": formatted_signals,
            "timestamp": _cache_timestamp.isoformat(),
            "count": len(formatted_signals),
            "buy_count": len([s for s in formatted_signals if s["signal"] == "BUY"]),
            "cached": False
        }
    except Exception as e:
        # Fallback to empty signals if pipeline fails
        print(f"Error fetching signals: {e}")
        import traceback
        traceback.print_exc()
        return {
            "success": False,
            "signals": [],
            "timestamp": datetime.utcnow().isoformat(),
            "count": 0,
            "error": str(e)
        }

@app.post("/signals/refresh")
async def refresh_signals(current_user: User = Depends(get_current_user)):
    """Refresh trading signals by running the full pipeline"""
    global _signals_cache, _cache_timestamp
    
    try:
        # Run the full pipeline (updates master data + generates signals)
        final_df, buy_signals = run_pipeline()
        
        # Get today's signals
        today = pd.to_datetime(date.today())
        today_signals = final_df[final_df['date'] == today]
        
        # Transform to frontend format
        formatted_signals = []
        for _, row in today_signals.iterrows():
            # Calculate change percentage
            change_pct = 0
            if "change_percent" in row and pd.notna(row["change_percent"]):
                change_pct = float(row["change_percent"])
            elif pd.notna(row.get("close")) and pd.notna(row.get("open")) and row.get("open") != 0:
                change_pct = ((float(row["close"]) - float(row["open"])) / float(row["open"])) * 100
            
            # Get previous day volume for 10% sell rule
            prev_vol = row.get("Prev_Volume")
            previous_day_volume = int(prev_vol) if pd.notna(prev_vol) else None
            
            formatted_signals.append({
                "symbol": row.get("symbol", "N/A"),
                "price": float(row.get("close", 0)),
                "change": round(change_pct, 2),
                "signal": row.get("Recommendation", "HOLD"),
                "quantity": calculate_recommended_quantity(row),
                "rsi": round(float(row.get("RSI", 0)), 2) if pd.notna(row.get("RSI")) else None,
                "ma50": round(float(row.get("MA50", 0)), 2) if pd.notna(row.get("MA50")) else None,
                "macd": round(float(row.get("MACD", 0)), 4) if pd.notna(row.get("MACD")) else None,
                "macd_signal": round(float(row.get("MACD_Signal", 0)), 4) if pd.notna(row.get("MACD_Signal")) else None,
                "volume": int(row.get("volume", 0)) if pd.notna(row.get("volume")) else None,
                "prev_volume": previous_day_volume,
                "previousDayVolume": previous_day_volume,
                "date": str(row.get("date")),
                "rsi_ok": bool(row.get("RSI_OK", False)),
                "ma_ok": bool(row.get("MA_OK", False)),
                "macd_ok": bool(row.get("MACD_OK", False)),
                "volume_ok": bool(row.get("VOLUME_OK", False))
            })
        
        # Update cache
        _signals_cache = formatted_signals
        _cache_timestamp = datetime.utcnow()
        
        return {
            "success": True,
            "signals": formatted_signals,
            "timestamp": _cache_timestamp.isoformat(),
            "count": len(formatted_signals),
            "buy_count": len(buy_signals),
            "total_processed": len(final_df),
            "message": "Signals refreshed successfully"
        }
    except Exception as e:
        print(f"Error refreshing signals: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to refresh signals: {str(e)}"
        )

# ============================================
# STOP LOSS POSITION MANAGEMENT (FIXED)
# ============================================

@app.post("/stop-loss/create")
async def create_stop_loss_position(
    position: StopLossCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a stop-loss position (for manually tracking positions)"""
    
    # Check if position already exists
    existing = db.query(StopLossPosition).filter(
        StopLossPosition.user_email == current_user.email,
        StopLossPosition.symbol == position.symbol,
        StopLossPosition.status.in_([StopLossStatus.ACTIVE, StopLossStatus.PARTIALLY_SOLD])
    ).first()
    
    if existing:
        quantity_sold = existing.quantity - existing.remaining_qty
        return {
            "success": True,
            "message": "Position already exists",
            "position": {
                "id": existing.id,
                "symbol": existing.symbol,
                "entry_price": existing.buy_price,
                "stop_loss_price": existing.stoploss,
                "quantity": existing.quantity,
                "remaining_qty": existing.remaining_qty,
                "quantity_sold": quantity_sold,
                "status": existing.status.value,
                "created_at": existing.created_at.isoformat()
            }
        }

    # Map frontend field names to database column names
    new_position = StopLossPosition(
        user_email=current_user.email,
        symbol=position.symbol,
        buy_price=position.entry_price,  # ✅ Map entry_price → buy_price
        stoploss=position.stop_loss_price,  # ✅ Map stop_loss_price → stoploss
        avg_price=position.avg_price if position.avg_price else position.entry_price,
        quantity=position.quantity,
        remaining_qty=position.quantity,  # ✅ FIX: Use remaining_qty not remaining_quantity
        status=StopLossStatus.ACTIVE
    )

    db.add(new_position)
    db.commit()
    db.refresh(new_position)

    return {
        "success": True,
        "message": "Stop-loss position created successfully",
        "position": {
            "id": new_position.id,
            "symbol": new_position.symbol,
            "entry_price": new_position.buy_price,
            "stop_loss_price": new_position.stoploss,
            "quantity": new_position.quantity,
            "remaining_qty": new_position.remaining_qty,
            "quantity_sold": 0,
            "status": new_position.status.value,
            "created_at": new_position.created_at.isoformat()
        }
    }
@app.get("/stop-loss/position/{symbol}")
async def get_stop_loss_position(
    symbol: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get active stop-loss position for a symbol"""
    position = db.query(StopLossPosition).filter(
        StopLossPosition.user_email == current_user.email,
        StopLossPosition.symbol == symbol,
        StopLossPosition.status.in_([StopLossStatus.ACTIVE, StopLossStatus.PARTIALLY_SOLD])
    ).first()
    
    if not position:
        return {
            "has_position": False,
            "position": None
        }
    
    # Get today's sells for this position
    today_start = datetime.combine(date.today(), datetime.min.time())
    today_sells = db.query(Order).filter(
        Order.user_email == current_user.email,
        Order.symbol == symbol,
        Order.order_type == OrderType.SELL,
        Order.created_at >= today_start
    ).all()
    
    sold_today = sum(o.quantity for o in today_sells)
    quantity_sold = position.quantity - position.remaining_qty  # Calculate sold amount
    
    return {
        "has_position": True,
        "position": {
            "id": position.id,
            "symbol": position.symbol,
            "total_quantity": position.quantity,  # Total originally bought
            "quantity_sold": quantity_sold,  # Calculate sold amount
            "remaining_quantity": position.remaining_qty,  # What's left to sell
            "entry_price": position.buy_price,  # Consistent naming
            "stop_loss_price": position.stoploss,  # Consistent naming
            "avg_price": position.avg_price,
            "status": position.status.value,
            "sold_today": sold_today
        }
    }

@app.patch("/stop-loss/update-sell/{symbol}")
async def update_stop_loss_after_sell(
    symbol: str,
    quantity_sold: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update stop-loss position after a sell order"""
    position = db.query(StopLossPosition).filter(
        StopLossPosition.user_email == current_user.email,
        StopLossPosition.symbol == symbol,
        StopLossPosition.status.in_([StopLossStatus.ACTIVE, StopLossStatus.PARTIALLY_SOLD])
    ).first()
    
    if not position:
        raise HTTPException(status_code=404, detail="Position not found")
    
    # Update quantities
    position.remaining_qty -= quantity_sold
    
    # Update status based on remaining quantity
    if position.remaining_qty <= 0:
        position.status = StopLossStatus.FULLY_SOLD
        position.remaining_qty = 0
    elif position.remaining_qty < position.quantity:
        position.status = StopLossStatus.PARTIALLY_SOLD
    
    position.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(position)
    
    return {
        "success": True,
        "message": f"Position updated - {quantity_sold} shares sold",
        "remaining": position.remaining_qty,
        "status": position.status.value
    }

@app.get("/stop-loss/all-positions")
async def get_all_positions(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all active stop-loss positions for current user"""
    positions = db.query(StopLossPosition).filter(
        StopLossPosition.user_email == current_user.email,
        StopLossPosition.status.in_([StopLossStatus.ACTIVE, StopLossStatus.PARTIALLY_SOLD])
    ).all()
    
    result = []
    for pos in positions:
        quantity_sold = pos.quantity - pos.remaining_qty
        result.append({
            "id": pos.id,
            "symbol": pos.symbol,
            "total_quantity": pos.quantity,
            "quantity_sold": quantity_sold,
            "remaining_quantity": pos.remaining_qty,
            "entry_price": pos.buy_price,
            "stop_loss_price": pos.stoploss,
            "avg_price": pos.avg_price,
            "status": pos.status.value,
            "created_at": pos.created_at.isoformat()
        })
    
    return {
        "success": True,
        "positions": result,
        "count": len(result)
    }

# ============================================
# ORDER ROUTES (Database-tracked)
# ============================================

@app.post("/orders/book-order")
async def book_order(
    order: OrderBooking,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    amount = order.quantity * order.price
    new_order = Order(
        user_email=current_user.email,
        symbol=order.symbol,
        quantity=order.quantity,
        price=order.price,
        amount=amount,
        order_type=OrderType[order.order_type],
        status="PENDING"
    )
    db.add(new_order)
    
    # If SELL order, update stop-loss position
    if order.order_type == "SELL":
        sl_position = db.query(StopLossPosition).filter(
            StopLossPosition.user_email == current_user.email,
            StopLossPosition.symbol == order.symbol,
            StopLossPosition.status.in_([StopLossStatus.ACTIVE, StopLossStatus.PARTIALLY_SOLD])
        ).first()
        
        if sl_position:
            # Update remaining quantity
            sl_position.remaining_qty -= order.quantity
            sl_position.updated_at = datetime.utcnow()
            
            # Update status
            if sl_position.remaining_qty <= 0:
                sl_position.status = StopLossStatus.FULLY_SOLD
                sl_position.remaining_qty = 0
            elif sl_position.remaining_qty < sl_position.quantity:
                sl_position.status = StopLossStatus.PARTIALLY_SOLD
    
    db.commit()
    db.refresh(new_order)

    # Get updated history
    history = await get_order_history(order.symbol, current_user, db)
    
    return {
        "success": True,
        "message": f"{order.order_type} order booked successfully",
        "order": {
            "id": new_order.id,
            "symbol": new_order.symbol,
            "quantity": new_order.quantity,
            "price": new_order.price,
            "amount": new_order.amount,
            "order_type": new_order.order_type.value,
            "created_at": new_order.created_at.isoformat()
        },
        "history": history
    }

@app.get("/orders/history/{symbol}")
async def get_order_history(
    symbol: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    orders = db.query(Order).filter(
        Order.user_email == current_user.email,
        Order.symbol == symbol
    ).order_by(Order.created_at.desc()).all()

    total_bought = sum(o.quantity for o in orders if o.order_type == OrderType.BUY)
    total_sold = sum(o.quantity for o in orders if o.order_type == OrderType.SELL)

    transactions = [
        {
            "id": o.id,
            "type": o.order_type.value,
            "quantity": o.quantity,
            "price": o.price,
            "amount": o.amount,
            "status": o.status,
            "timestamp": o.created_at.isoformat()
        }
        for o in orders
    ]

    return {
        "symbol": symbol,
        "total_bought": total_bought,
        "total_sold": total_sold,
        "net_position": total_bought - total_sold,
        "transactions": transactions
    }

@app.get("/orders/all-history")
async def get_all_order_history(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    summary = db.query(
        Order.symbol,
        func.sum(func.case((Order.order_type == OrderType.BUY, Order.quantity), else_=0)).label('total_bought'),
        func.sum(func.case((Order.order_type == OrderType.SELL, Order.quantity), else_=0)).label('total_sold'),
        func.count(Order.id).label('order_count')
    ).filter(
        Order.user_email == current_user.email
    ).group_by(Order.symbol).all()

    result = {}
    for row in summary:
        result[row.symbol] = {
            "symbol": row.symbol,
            "total_bought": row.total_bought or 0,
            "total_sold": row.total_sold or 0,
            "net_position": (row.total_bought or 0) - (row.total_sold or 0),
            "order_count": row.order_count
        }

    return {
        "user": current_user.email,
        "orders": result,
        "total_positions": len(result)
    }

@app.get("/orders/today-summary")
async def get_today_summary(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    today_start = datetime.combine(date.today(), datetime.min.time())

    orders_today = db.query(Order).filter(
        Order.user_email == current_user.email,
        Order.created_at >= today_start
    ).all()

    buy_orders = [o for o in orders_today if o.order_type == OrderType.BUY]
    sell_orders = [o for o in orders_today if o.order_type == OrderType.SELL]

    return {
        "date": str(date.today()),
        "total_orders": len(orders_today),
        "buy_orders": len(buy_orders),
        "sell_orders": len(sell_orders),
        "total_buy_amount": sum(o.amount for o in buy_orders),
        "total_sell_amount": sum(o.amount for o in sell_orders),
        "orders": [
            {
                "id": o.id,
                "symbol": o.symbol,
                "type": o.order_type.value,
                "quantity": o.quantity,
                "price": o.price,
                "amount": o.amount,
                "time": o.created_at.strftime("%H:%M:%S")
            }
            for o in orders_today
        ]
    }

# Health Check
@app.get("/health")
def health_check():
    return {"status": "ok"}

# Initialize database tables
Base.metadata.create_all(bind=engine)