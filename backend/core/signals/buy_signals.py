# # signals/buy_signal.py
# import pandas as pd
# from backend.core.technical_indicators.technicals import calculate_indicators

# def check_buy_conditions(data: pd.DataFrame) -> pd.DataFrame:
#     """Apply PO's Buy conditions to stock data."""
#     # Individual conditions
#     data['RSI_OK'] = data['RSI'] >= 60
#     data['MA_OK'] = data['close'] > data['MA50']
#     data['MACD_OK'] = data['MACD'] > data['MACD_Signal']
#     data['VOLUME_OK'] = data['volume'] >= 1.1 * data['Prev_Volume']

#     # Final decision: all must be True
#     data['Buy_Signal'] = data['RSI_OK'] & data['MA_OK'] & data['MACD_OK'] & data['VOLUME_OK']

#     # Recommendation
#     data['Recommendation'] = data['Buy_Signal'].apply(lambda x: "BUY" if x else "REJECT")

#     return data


# def generate_buy_signals(df: pd.DataFrame) -> pd.DataFrame:
#     """
#     Process all symbols and return DataFrame with Buy/Reject signals.
#     Keeps individual conditions for audit/debug.
#     """
#     results = []
#     for symbol, data in df.groupby("symbol"):
#         data = data.sort_values(by="date").copy()

#         # Calculate technical indicators first
#         data = calculate_indicators(data)

#         # Apply buy/reject logic
#         data = check_buy_conditions(data)

#         results.append(data)

#     # Concatenate all symbols
#     return pd.concat(results).reset_index(drop=True)


# backend/core/signals/buy_signals.py
import pandas as pd
from backend.core.technical_indicators.technicals import calculate_indicators

def check_buy_conditions(
    data: pd.DataFrame,
    enable_rsi: bool = True,
    enable_ma: bool = True,
    enable_macd: bool = True,
    enable_volume: bool = True
) -> pd.DataFrame:
    """
    Apply PO's FIXED Buy conditions to stock data.
    
    PO's Fixed Rules (NOT adjustable):
    - RSI >= 60 (FIXED threshold)
    - Close > MA50 (FIXED threshold)
    - MACD > MACD_Signal (FIXED rule)
    - Volume >= 1.1 × Prev_Volume (FIXED threshold)
    
    What IS adjustable:
    - Which indicators to CHECK (enable/disable via sidebar)
    
    Args:
        data: DataFrame with technical indicators calculated
        enable_rsi: Whether to check RSI (default: True)
        enable_ma: Whether to check MA50 (default: True)
        enable_macd: Whether to check MACD (default: True)
        enable_volume: Whether to check Volume (default: True)
    
    Returns:
        DataFrame with buy signal columns added
    """
    # PO's FIXED RULES - Thresholds NEVER change
    data['RSI_OK'] = data['RSI'] >= 60
    data['MA_OK'] = data['close'] > data['MA50']
    data['MACD_OK'] = data['MACD'] > data['MACD_Signal']
    data['VOLUME_OK'] = data['volume'] >= (1.1 * data['Prev_Volume'])
    
    # Build buy signal based on which checks are ENABLED
    conditions = []
    
    if enable_rsi:
        conditions.append(data['RSI_OK'])
    else:
        data['RSI_OK'] = True  # Pass by default if disabled
    
    if enable_ma:
        conditions.append(data['MA_OK'])
    else:
        data['MA_OK'] = True  # Pass by default if disabled
    
    if enable_macd:
        conditions.append(data['MACD_OK'])
    else:
        data['MACD_OK'] = True  # Pass by default if disabled
    
    if enable_volume:
        conditions.append(data['VOLUME_OK'])
    else:
        data['VOLUME_OK'] = True  # Pass by default if disabled
    
    # All ENABLED conditions must be True
    if len(conditions) > 0:
        data['Buy_Signal'] = pd.concat(conditions, axis=1).all(axis=1)
    else:
        # If all disabled, reject everything (safety)
        data['Buy_Signal'] = False
    
    # Generate detailed recommendation with reason
    def get_recommendation(row):
        # Check ENABLED indicators in priority order
        if enable_rsi and not row['RSI_OK']:
            return f"REJECT - RSI {row['RSI']:.1f} < 60"
        
        if enable_macd and not row['MACD_OK']:
            return "REJECT - MACD below Signal"
        
        if enable_ma and not row['MA_OK']:
            return "REJECT - Price below MA50"
        
        if enable_volume and not row['VOLUME_OK']:
            return "REJECT - Volume < 1.1× Previous"
        
        # All ENABLED checks passed
        if row['Buy_Signal']:
            return "BUY"
        
        return "REJECT"
    
    data['Recommendation'] = data.apply(get_recommendation, axis=1)
    
    # Add metadata about what was checked
    data['check_rsi'] = enable_rsi
    data['check_ma'] = enable_ma
    data['check_macd'] = enable_macd
    data['check_volume'] = enable_volume
    
    return data


def generate_buy_signals(
    df: pd.DataFrame,
    rsi_threshold: float = 60.0, 
    ma_buffer: float = 0.0,          
    volume_multiplier: float = 1.1,
    enable_rsi: bool = True,
    enable_ma: bool = True,
    enable_macd: bool = True,
    enable_volume: bool = True
) -> pd.DataFrame:
    """
    Process all symbols and return DataFrame with Buy/Reject signals.
    
    Uses PO's FIXED rules:
    - RSI >= 60 (FIXED)
    - Close > MA50 (FIXED)
    - MACD > MACD_Signal (FIXED)
    - Volume >= 1.1 × Prev_Volume (FIXED)
    
    What's configurable:
    - Which indicators to CHECK (enable/disable from sidebar)
    
    Args:
        df: DataFrame with OHLCV data
        enable_rsi: Check RSI condition (default: True)
        enable_ma: Check MA50 condition (default: True)
        enable_macd: Check MACD condition (default: True)
        enable_volume: Check Volume condition (default: True)
    
    Returns:
        DataFrame with signals and individual condition checks
    """
    results = []
    
    for symbol, data in df.groupby("symbol"):
        data = data.sort_values(by="date").copy()
        
        # Step 1: Calculate technical indicators
        data = calculate_indicators(data)
        
        # Step 2: Apply buy/reject logic with indicator toggles
        data = check_buy_conditions(
            data,
            enable_rsi=enable_rsi,
            enable_ma=enable_ma,
            enable_macd=enable_macd,
            enable_volume=enable_volume
        )
        
        results.append(data)
    
    # Concatenate all symbols
    final_df = pd.concat(results).reset_index(drop=True)
    
    # Log summary
    buy_count = len(final_df[final_df['Recommendation'] == 'BUY'])
    reject_count = len(final_df[final_df['Recommendation'].str.startswith('REJECT')])
    
    # Show which indicators are active
    active_indicators = []
    if enable_rsi:
        active_indicators.append("RSI >= 60")
    if enable_ma:
        active_indicators.append("Close > MA50")
    if enable_macd:
        active_indicators.append("MACD > Signal")
    if enable_volume:
        active_indicators.append("Volume >= 1.1× Prev")
    
    print(f"[INFO] Signal Generation Complete:")
    print(f"   - Active Indicators: {', '.join(active_indicators) if active_indicators else 'NONE (All disabled)'}")
    print(f"   - BUY Signals: {buy_count}")
    print(f"   - REJECT Signals: {reject_count}")
    
    return final_df