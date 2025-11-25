# backend/core/trading/sell_routes.py

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timedelta
import pandas as pd

# IMPORT FROM dependencies.py (NOT from main.py)
from backend.core.auth.dependencies import get_current_user, get_db
from backend.core.auth.models import User, Transaction, Position
from backend.core.signals.sell_signals import (
    generate_sell_signals,
    check_positions_for_sell,
    get_sell_recommendations
)
from backend.core.technical_indicators.technicals import calculate_indicators

router = APIRouter(prefix="/sell-signals", tags=["sell-signals"])


@router.get("/today")
def get_today_sell_signals(
    current_user: User = Depends(get_current_user),  # NOW THIS WORKS!
    db: Session = Depends(get_db)
):
    """
    Get today's sell signals for all stocks
    """
    try:
        master_data_path = "D:/Trading_system/backend/core/data/master_data.csv"
        df = pd.read_csv(master_data_path)
        df['date'] = pd.to_datetime(df['date'])
        
        # Calculate indicators
        symbols_data = []
        for symbol in df['symbol'].unique():
            symbol_df = df[df['symbol'] == symbol].sort_values('date').copy()
            symbol_df = calculate_indicators(symbol_df)
            symbols_data.append(symbol_df)
        
        master_df = pd.concat(symbols_data, ignore_index=True)
        
        # Generate sell signals
        all_signals, sell_signals = generate_sell_signals(master_df)
        
        return {
            "status": "success",
            "total_stocks": len(all_signals),
            "sell_signals_count": len(sell_signals),
            "signals": sell_signals.to_dict('records') if not sell_signals.empty else []
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating sell signals: {str(e)}")


@router.get("/recommendations")
def get_sell_signal_recommendations(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get sell signal recommendations with breakdown by type
    """
    try:
        master_data_path = "D:/Trading_system/backend/core/data/master_data.csv"
        df = pd.read_csv(master_data_path)
        df['date'] = pd.to_datetime(df['date'])
        
        # Calculate indicators
        symbols_data = []
        for symbol in df['symbol'].unique():
            symbol_df = df[df['symbol'] == symbol].sort_values('date').copy()
            symbol_df = calculate_indicators(symbol_df)
            symbols_data.append(symbol_df)
        
        master_df = pd.concat(symbols_data, ignore_index=True)
        
        # Get recommendations
        recommendations = get_sell_recommendations(master_df)
        
        return {
            "status": "success",
            "summary": {
                "total_sell_signals": recommendations['total_sell_signals'],
                "by_type": {
                    "macd_sells": recommendations['macd_sells'],
                    "rsi_sells": recommendations['rsi_sells'],
                    "stop_loss_hits": recommendations['sl_hits']
                }
            },
            "signals": recommendations['signals']
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting recommendations: {str(e)}")