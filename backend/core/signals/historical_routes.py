
# BACKEND\core\signals\historical_routes.py


from fastapi import APIRouter, Depends, HTTPException, Query
from datetime import datetime, timedelta
import pandas as pd
import os
from typing import Optional
from pydantic import BaseModel
from core.auth.dependencies import get_current_user
from core.auth.models import User

router = APIRouter(prefix="/api/signals", tags=["signals"])


@router.get("/historical")
async def get_historical_signals(
    start_date: Optional[str] = Query(None, description="Start date YYYY-MM-DD"),
    end_date: Optional[str] = Query(None, description="End date YYYY-MM-DD"),
    recommendation: Optional[str] = Query(None, description="BUY or SELL"),
    current_user: User = Depends(get_current_user)
):
    """
    Fetch historical signals for the last 14 days from master_data.csv
    
    Query Parameters:
    - start_date: YYYY-MM-DD (default: 14 days ago)
    - end_date: YYYY-MM-DD (default: today)
    - recommendation: BUY, SELL, or leave empty for all
    """
    try:
        # Set default dates
        if not end_date:
            end_date = datetime.now().strftime('%Y-%m-%d')
        if not start_date:
            start_date = (datetime.now() - timedelta(days=14)).strftime('%Y-%m-%d')
        
        # Parse dates
        start_date_obj = datetime.strptime(start_date, '%Y-%m-%d').date()
        end_date_obj = datetime.strptime(end_date, '%Y-%m-%d').date()
        
        # Load master data CSV from core/data directory
        csv_path = os.path.join('core', 'data', 'master_data.csv')
        if not os.path.exists(csv_path):
            raise HTTPException(status_code=404, detail="Master data file not found")
        
        df = pd.read_csv(csv_path)
        
        # Convert date column to datetime
        df['date'] = pd.to_datetime(df['date'])
        
        # Filter by date range (last 14 days)
        mask = (df['date'].dt.date >= start_date_obj) & (df['date'].dt.date <= end_date_obj)
        df_filtered = df[mask].copy()
        
        # Filter by recommendation if specified
        if recommendation:
            df_filtered = df_filtered[df_filtered['recommendation'] == recommendation.upper()]
        
        # Sort by date descending (most recent first)
        df_filtered = df_filtered.sort_values('date', ascending=False)
        
        # Convert to list of dictionaries
        signals = []
        for _, row in df_filtered.iterrows():
            # Calculate indicator checks (✓ or ✗)
            rsi_ok = False
            ma_ok = False
            macd_ok = False
            volume_ok = False
            
            # RSI check (BUY if RSI >= 60)
            if pd.notna(row.get('rsi')):
                rsi_ok = float(row['rsi']) >= 60
            
            # MA50 check (BUY if close > ma_50)
            if pd.notna(row.get('close')) and pd.notna(row.get('ma_50')):
                ma_ok = float(row['close']) > float(row['ma_50'])
            
            # MACD check (BUY if macd > 0)
            if pd.notna(row.get('macd')):
                macd_ok = float(row['macd']) > 0
            
            # Volume check
            if pd.notna(row.get('volume')):
                volume_ok = True
            
            signal_data = {
                'date': row['date'].strftime('%Y-%m-%d'),
                'symbol': row['symbol'],
                'close': float(row['close']) if pd.notna(row['close']) else None,
                'price': float(row['close']) if pd.notna(row['close']) else None,
                'rsi': float(row['rsi']) if pd.notna(row['rsi']) else None,
                'ma_50': float(row['ma_50']) if pd.notna(row['ma_50']) else None,
                'ma50': float(row['ma_50']) if pd.notna(row['ma_50']) else None,
                'macd': float(row['macd']) if pd.notna(row['macd']) else None,
                'volume': int(row['volume']) if pd.notna(row['volume']) else None,
                'recommendation': row['recommendation'],
                'signal': row['recommendation'],
                'industry': row.get('industry', 'N/A'),
                # Add indicator check results
                'rsi_ok': rsi_ok,
                'ma_ok': ma_ok,
                'macd_ok': macd_ok,
                'volume_ok': volume_ok
            }
            signals.append(signal_data)
        
        return {
            'success': True,
            'signals': signals,
            'count': len(signals),
            'start_date': start_date,
            'end_date': end_date,
            'filter': recommendation or 'all'
        }
        
    except Exception as e:
        print(f"Error fetching historical signals: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


class RecalculateRequest(BaseModel):
    rsi_threshold: float = 60
    ma_buffer: float = 0
    volume_multiplier: float = 1.1
    enable_rsi: bool = True
    enable_ma: bool = True
    enable_macd: bool = True
    enable_volume: bool = True


@router.post("/recalculate")
async def recalculate_signals(
    request: RecalculateRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Recalculate signals with custom thresholds (for Dynamic Backtester)
    """
    try:
        # Load master data CSV from core/data directory
        csv_path = os.path.join('core', 'data', 'master_data.csv')
        if not os.path.exists(csv_path):
            raise HTTPException(status_code=404, detail="Master data file not found")
        
        df = pd.read_csv(csv_path)
        df['date'] = pd.to_datetime(df['date'])
        
        # Get today's data only for backtesting comparison
        today = datetime.now().date()
        df_today = df[df['date'].dt.date == today].copy()
        
        # Original recommendation
        original_summary = {
            'buy_count': int(len(df_today[df_today['recommendation'] == 'BUY'])),
            'reject_count': int(len(df_today[df_today['recommendation'] == 'REJECT']))
        }
        
        # Recalculate with new thresholds
        def calculate_new_recommendation(row):
            checks = []
            
            if request.enable_rsi and pd.notna(row['rsi']):
                checks.append(row['rsi'] >= request.rsi_threshold)
            
            if request.enable_ma and pd.notna(row['close']) and pd.notna(row['ma_50']):
                ma_threshold = row['ma_50'] * (1 + request.ma_buffer / 100)
                checks.append(row['close'] > ma_threshold)
            
            if request.enable_macd and pd.notna(row['macd']):
                checks.append(row['macd'] > 0)
            
            if request.enable_volume and pd.notna(row['volume']):
                checks.append(True)
            
            # If all enabled checks pass, return BUY
            return 'BUY' if (len(checks) > 0 and all(checks)) else 'REJECT'
        
        df_today['new_recommendation'] = df_today.apply(calculate_new_recommendation, axis=1)
        
        new_summary = {
            'buy_count': int(len(df_today[df_today['new_recommendation'] == 'BUY'])),
            'reject_count': int(len(df_today[df_today['new_recommendation'] == 'REJECT']))
        }
        
        # Calculate changes
        new_buys = int(len(df_today[(df_today['recommendation'] == 'REJECT') & (df_today['new_recommendation'] == 'BUY')]))
        lost_buys = int(len(df_today[(df_today['recommendation'] == 'BUY') & (df_today['new_recommendation'] == 'REJECT')]))
        
        # Prepare comparison data
        comparison_data = []
        for _, row in df_today.iterrows():
            comparison_data.append({
                'symbol': row['symbol'],
                'price': float(row['close']),
                'rsi': float(row['rsi']) if pd.notna(row['rsi']) else None,
                'ma50': float(row['ma_50']) if pd.notna(row['ma_50']) else None,
                'macd': float(row['macd']) if pd.notna(row['macd']) else None,
                'volume': int(row['volume']) if pd.notna(row['volume']) else None,
                'original': {
                    'recommendation': row['recommendation']
                },
                'new': {
                    'recommendation': row['new_recommendation']
                },
                'changed': bool(row['recommendation'] != row['new_recommendation'])
            })
        
        return {
            'success': True,
            'original_summary': original_summary,
            'new_summary': new_summary,
            'changes': {
                'new_buys': new_buys,
                'lost_buys': lost_buys,
                'total_changed': new_buys + lost_buys
            },
            'comparison_data': comparison_data,
            'thresholds_used': {
                'rsi_threshold': request.rsi_threshold,
                'ma_buffer': request.ma_buffer,
                'volume_multiplier': request.volume_multiplier,
                'enable_rsi': request.enable_rsi,
                'enable_ma': request.enable_ma,
                'enable_macd': request.enable_macd,
                'enable_volume': request.enable_volume
            }
        }
        
    except Exception as e:
        print(f"Error recalculating signals: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))