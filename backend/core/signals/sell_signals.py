# backend/core/signals/sell_signals.py
"""
Sell Signal Generation Logic
PO-approved rules:
Step 1: MACD Sell Signal (MACD crosses below Signal line)
Step 2: RSI < 50
Step 3: Stop-Loss Hit (Price <= Stop-Loss Price)
"""

import pandas as pd
from datetime import datetime
from typing import Dict, List, Tuple

def generate_sell_signals(
    df: pd.DataFrame,
    positions_df: pd.DataFrame = None
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Generate sell signals based on PO's sequential logic
    
    Args:
        df: DataFrame with OHLCV data and technical indicators
        positions_df: DataFrame with current user positions (optional)
    
    Returns:
        Tuple of (all_signals_df, sell_signals_df)
    """
    
    if df is None or df.empty:
        return pd.DataFrame(), pd.DataFrame()
    
    # Ensure we have the latest data per symbol
    df_latest = df.sort_values('date').groupby('symbol').tail(1).copy()
    
    # Initialize columns
    df_latest['sell_signal'] = 'HOLD'
    df_latest['sell_reason'] = ''
    df_latest['macd_sell'] = False
    df_latest['rsi_sell'] = False
    df_latest['sl_hit'] = False
    
    for idx, row in df_latest.iterrows():
        symbol = row['symbol']
        
        # Step 1: Check MACD Sell Signal (MACD crosses below Signal line)
        # MACD Sell = Current MACD < Current Signal AND Previous MACD >= Previous Signal
        macd_current = row.get('MACD', 0)
        signal_current = row.get('MACD_Signal', 0)
        
        # Get previous values for crossover detection
        symbol_data = df[df['symbol'] == symbol].sort_values('date').tail(2)
        if len(symbol_data) >= 2:
            prev_macd = symbol_data.iloc[-2].get('MACD', 0)
            prev_signal = symbol_data.iloc[-2].get('MACD_Signal', 0)
            
            # MACD Sell: crosses below signal line
            macd_sell = (macd_current < signal_current) and (prev_macd >= prev_signal)
        else:
            macd_sell = macd_current < signal_current
        
        df_latest.at[idx, 'macd_sell'] = macd_sell
        
        if macd_sell:
            df_latest.at[idx, 'sell_signal'] = 'SELL'
            df_latest.at[idx, 'sell_reason'] = 'MACD Sell Signal'
            continue  # MACD sell is highest priority
        
        # Step 2: Check RSI < 50
        rsi = row.get('RSI', 50)
        rsi_sell = rsi < 50
        df_latest.at[idx, 'rsi_sell'] = rsi_sell
        
        if rsi_sell:
            df_latest.at[idx, 'sell_signal'] = 'SELL'
            df_latest.at[idx, 'sell_reason'] = 'RSI < 50'
            continue
        
        # Step 3: Check Stop-Loss Hit (if positions data provided)
        if positions_df is not None and not positions_df.empty:
            position = positions_df[positions_df['symbol'] == symbol]
            if not position.empty:
                current_price = row.get('close', 0)
                stop_loss = position.iloc[0].get('sl_price', 0)
                
                sl_hit = current_price <= stop_loss if stop_loss > 0 else False
                df_latest.at[idx, 'sl_hit'] = sl_hit
                
                if sl_hit:
                    df_latest.at[idx, 'sell_signal'] = 'SELL'
                    df_latest.at[idx, 'sell_reason'] = 'Stop-Loss Hit'
                    continue
    
    # Filter only SELL signals
    sell_signals = df_latest[df_latest['sell_signal'] == 'SELL'].copy()
    
    # Select relevant columns for sell signals
    sell_columns = [
        'date', 'symbol', 'close', 'sell_signal', 'sell_reason',
        'RSI', 'MACD', 'MACD_Signal', 'MA_50',
        'macd_sell', 'rsi_sell', 'sl_hit'
    ]
    
    # Only include columns that exist
    available_columns = [col for col in sell_columns if col in sell_signals.columns]
    sell_signals_final = sell_signals[available_columns].copy()
    
    return df_latest, sell_signals_final


def check_positions_for_sell(positions_df: pd.DataFrame, market_data_df: pd.DataFrame) -> pd.DataFrame:
    """
    Check existing positions against current market data for sell signals
    
    Args:
        positions_df: DataFrame with columns [symbol, quantity, buy_price, sl_price]
        market_data_df: DataFrame with current market data and indicators
    
    Returns:
        DataFrame with positions that have sell signals
    """
    
    if positions_df is None or positions_df.empty:
        return pd.DataFrame()
    
    if market_data_df is None or market_data_df.empty:
        return pd.DataFrame()
    
    sell_positions = []
    
    for idx, position in positions_df.iterrows():
        symbol = position['symbol']
        sl_price = position.get('sl_price', 0)
        buy_price = position.get('buy_price', 0)
        quantity = position.get('quantity', 0)
        
        # Get current market data for this symbol
        market_data = market_data_df[market_data_df['symbol'] == symbol]
        
        if market_data.empty:
            continue
        
        current_data = market_data.iloc[-1]
        current_price = current_data.get('close', 0)
        rsi = current_data.get('RSI', 50)
        macd = current_data.get('MACD', 0)
        macd_signal = current_data.get('MACD_Signal', 0)
        
        sell_reason = None
        priority = 0
        
        # Step 1: MACD Sell (Highest Priority)
        if len(market_data) >= 2:
            prev_data = market_data.iloc[-2]
            prev_macd = prev_data.get('MACD', 0)
            prev_signal = prev_data.get('MACD_Signal', 0)
            
            if (macd < macd_signal) and (prev_macd >= prev_signal):
                sell_reason = 'MACD Sell Signal'
                priority = 1
        
        # Step 2: RSI < 50
        if sell_reason is None and rsi < 50:
            sell_reason = 'RSI < 50'
            priority = 2
        
        # Step 3: Stop-Loss Hit
        if sell_reason is None and sl_price > 0 and current_price <= sl_price:
            sell_reason = 'Stop-Loss Hit'
            priority = 3
        
        if sell_reason:
            sell_positions.append({
                'symbol': symbol,
                'quantity': quantity,
                'buy_price': buy_price,
                'current_price': current_price,
                'sl_price': sl_price,
                'sell_reason': sell_reason,
                'priority': priority,
                'rsi': rsi,
                'macd': macd,
                'macd_signal': macd_signal,
                'potential_loss': (current_price - buy_price) * quantity,
                'loss_percent': ((current_price - buy_price) / buy_price) * 100,
                'date': current_data.get('date', datetime.now())
            })
    
    if sell_positions:
        sell_df = pd.DataFrame(sell_positions)
        # Sort by priority (MACD=1, RSI=2, SL=3)
        sell_df = sell_df.sort_values('priority').reset_index(drop=True)
        return sell_df
    
    return pd.DataFrame()


def get_sell_recommendations(df: pd.DataFrame) -> Dict:
    """
    Get sell signal recommendations summary
    
    Args:
        df: DataFrame with market data and indicators
    
    Returns:
        Dictionary with sell signal statistics
    """
    
    _, sell_signals = generate_sell_signals(df)
    
    if sell_signals.empty:
        return {
            'total_sell_signals': 0,
            'macd_sells': 0,
            'rsi_sells': 0,
            'sl_hits': 0,
            'signals': []
        }
    
    summary = {
        'total_sell_signals': len(sell_signals),
        'macd_sells': int(sell_signals['macd_sell'].sum()) if 'macd_sell' in sell_signals.columns else 0,
        'rsi_sells': int(sell_signals['rsi_sell'].sum()) if 'rsi_sell' in sell_signals.columns else 0,
        'sl_hits': int(sell_signals['sl_hit'].sum()) if 'sl_hit' in sell_signals.columns else 0,
        'signals': sell_signals.to_dict('records')
    }
    
    return summary
