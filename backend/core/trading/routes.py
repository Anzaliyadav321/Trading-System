# backend/core/trading/routes.py
from fastapi import APIRouter, Depends, HTTPException
from jose import jwt, JWTError
from datetime import datetime
from fastapi.security import OAuth2PasswordBearer
from backend.core.security import SECRET_KEY, ALGORITHM

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
