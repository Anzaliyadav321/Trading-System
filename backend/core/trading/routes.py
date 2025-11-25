# backend/core/trading/routes.py
from fastapi import APIRouter, Depends, HTTPException
from jose import jwt, JWTError
from datetime import datetime
from fastapi.security import OAuth2PasswordBearer
from backend.core.security import SECRET_KEY, ALGORITHM
from sqlalchemy.orm import Session
from core.database import get_db
from core.auth.models import Transaction, TransactionItem
from core.auth.schemas import TransactionCreate, TransactionResponse
from core.security import get_current_user

router = APIRouter(prefix="/orders", tags=["Orders"])

# In-memory storage (you can later move this to a database)
logs = []
orders = []
cash_balance = 100000  # example starting balance

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

@router.post("/book")
def book_order(order: dict, token: str = Depends(oauth2_scheme)):
    """Place a buy order (authenticated)"""
    try:
        jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

    msg = f"Placing buy order for {order['qty']} of {order['symbol']} at {order['price']}"
    logs.append({"time": datetime.now().strftime("%H:%M:%S"), "msg": msg})
    orders.append(order)
    return {"message": msg}


@router.post("/confirm/{symbol}")
def confirm_order(symbol: str, token: str = Depends(oauth2_scheme)):
    """Confirm order and deduct from cash balance (authenticated)"""
    global cash_balance
    try:
        jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

    try:
        order = next(o for o in orders if o["symbol"] == symbol)
    except StopIteration:
        raise HTTPException(status_code=404, detail=f"No order found for {symbol}")

    amount = order["qty"] * order["price"]
    cash_balance -= amount
    logs.append({
        "time": datetime.now().strftime("%H:%M:%S"),
        "msg": f"Order confirmed: {symbol} @ {order['price']} x {order['qty']}"
    })
    return {"message": "Order confirmed", "balance": cash_balance}


# backend/core/trading/routes.py (update your transaction endpoints)

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from core.database import get_db
from core.auth.models import Transaction, TransactionItem
from core.auth.schemas import TransactionCreate, TransactionResponse
from core.security import get_current_user

router = APIRouter(prefix="/transactions", tags=["transactions"])

@router.post("/", response_model=TransactionResponse)
def create_transaction(
    transaction_data: TransactionCreate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create transaction with bill details"""
    
    total_amount = transaction_data.quantity * transaction_data.price
    
    new_transaction = Transaction(
        user_id=current_user["id"],
        symbol=transaction_data.symbol,
        transaction_type=transaction_data.transaction_type,
        quantity=transaction_data.quantity,
        price=transaction_data.price,
        total_amount=total_amount,
        stop_loss_price=transaction_data.stop_loss_price,
        notes=transaction_data.notes,
        
        # NEW: Bill details
        bill_number=transaction_data.bill_number,
        bill_date=transaction_data.bill_date,
        sub_total=transaction_data.sub_total,
        grand_total=transaction_data.grand_total,
        share_amount=transaction_data.share_amount,
        share_quantity=transaction_data.share_quantity,
        sebn_commission=transaction_data.sebn_commission,
        nepse_commission=transaction_data.nepse_commission,
        sebon_regulatory_fee=transaction_data.sebon_regulatory_fee,
        broker_commission=transaction_data.broker_commission,
        name_transfer_amount=transaction_data.name_transfer_amount,
        dp_amount=transaction_data.dp_amount,
        total_commission=transaction_data.total_commission,
        clearance_date=transaction_data.clearance_date,
        net_receivable_amount=transaction_data.net_receivable_amount,
        broker_name=transaction_data.broker_name,
        broker_number=transaction_data.broker_number
    )
    
    db.add(new_transaction)
    db.flush()
    
    # Add items
    if transaction_data.items:
        for item in transaction_data.items:
            transaction_item = TransactionItem(
                transaction_id=new_transaction.id,
                **item.dict()
            )
            db.add(transaction_item)
    
    db.commit()
    db.refresh(new_transaction)
    
    return new_transaction
