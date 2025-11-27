# backend/core/signals/buy_signals.py
import pandas as pd
from core.technical_indicators.technicals import calculate_indicators

def check_buy_conditions(
    data: pd.DataFrame,
    rsi_threshold: float = 60.0,
    ma_buffer: float = 0.0,
    volume_multiplier: float = 1.1,
    enable_rsi: bool = True,
    enable_ma: bool = True,
    enable_macd: bool = True,
    enable_volume: bool = True  # Still accepts parameter for backward compatibility
) -> pd.DataFrame:
    """
    Apply PO's EXACT Buy conditions with SEQUENTIAL CHECKS.
    
    SEQUENTIAL BUY LOGIC (Step-by-step filter):
    Step 1: MA Check - If fails → REJECT (don't check further)
    Step 2: RSI Check - If fails → REJECT (don't check MACD)
    Step 3: MACD Check - If fails → REJECT, If passes → BUY
    
    NOTE: Volume is NOT used for signal generation.
    Volume is only used for quantity calculation in the Executor.
    
    Technical Indicators:
    - MA: Close >= 50-day Moving Average
    - RSI: RSI >= 60
    - MACD: MACD line > Signal line (standard buy signal as shown on websites)
    
    Args:
        data: DataFrame with technical indicators calculated
        rsi_threshold: RSI threshold (default: 60)
        ma_buffer: MA50 buffer percentage (default: 0)
        volume_multiplier: Volume multiplier (kept for data tracking, not used in signals)
        enable_rsi: Whether to check RSI (default: True)
        enable_ma: Whether to check MA50 (default: True)
        enable_macd: Whether to check MACD (default: True)
        enable_volume: Kept for backward compatibility, not used in signal logic
    
    Returns:
        DataFrame with buy signal columns added
    """
    # Calculate individual conditions
    data['RSI_OK'] = (data['RSI'] >= rsi_threshold) if enable_rsi else False
    data['MA_OK'] = (data['close'] >= data['MA50'] * (1 + ma_buffer/100)) if enable_ma else False
    data['MACD_OK'] = (data['MACD'] > data['MACD_Signal']) if enable_macd else False
    
    # Calculate volume condition for data tracking (NOT used in signal decision)
    data['VOLUME_OK'] = (data['volume'] >= data['Prev_Volume'] * volume_multiplier)
    
    def determine_signal(row):
        """
        Apply PO's SEQUENTIAL buy logic.
        
        Step 1: Check MA first
        Step 2: Check RSI (only if MA passed)
        Step 3: Check MACD (only if MA and RSI passed)
        
        If ANY step fails → REJECT immediately, don't check next steps
        """
        
        # Step 1: Check MA FIRST
        if not row['MA_OK']:
            return 'REJECT'  # Failed Step 1, stop here
        
        # Step 2: Check RSI (only reached if MA passed)
        if not row['RSI_OK']:
            return 'REJECT'  # Failed Step 2, stop here
        
        # Step 3: Check MACD (only reached if MA and RSI passed)
        if row['MACD_OK']:
            return 'BUY'  # Passed all 3 steps
        else:
            return 'REJECT'  # Failed Step 3
    
    # Apply the combination logic
    data['Recommendation'] = data.apply(determine_signal, axis=1)
    data['Buy_Signal'] = data['Recommendation'] == 'BUY'
    
    # Add metadata about what was checked
    data['check_rsi'] = enable_rsi
    data['check_ma'] = enable_ma
    data['check_macd'] = enable_macd
    data['check_volume'] = enable_volume  # Kept for compatibility
    
    return data


def generate_buy_signals(
    df: pd.DataFrame,
    rsi_threshold: float = 60.0, 
    ma_buffer: float = 0.0,          
    volume_multiplier: float = 1.1,
    enable_rsi: bool = True,
    enable_ma: bool = True,
    enable_macd: bool = True,
    enable_volume: bool = True  # Kept for backward compatibility
) -> pd.DataFrame:
    """
    Process all symbols and return DataFrame with Buy/Reject signals.
    
    Uses PO's SEQUENTIAL combination rule:
    Step 1: MA → Step 2: RSI → Step 3: MACD → BUY
    (If any step fails → REJECT)
    
    Volume is calculated but NOT used for signal generation.
    Volume is used later in Executor for quantity calculation (10% rule).
    
    Technical Indicators Checked:
    - MA50: Close >= 50-day Moving Average (checked FIRST)
    - RSI: RSI >= 60 (checked SECOND)
    - MACD: MACD line > Signal line (checked THIRD)
    
    Args:
        df: DataFrame with OHLCV data (should include full historical data per symbol)
        rsi_threshold: RSI threshold (default: 60)
        ma_buffer: MA50 buffer % (default: 0)
        volume_multiplier: Volume multiplier (tracked but not used in signals)
        enable_rsi: Check RSI condition (default: True)
        enable_ma: Check MA50 condition (default: True)
        enable_macd: Check MACD condition (default: True)
        enable_volume: Kept for backward compatibility (not used in signal logic)
    
    Returns:
        DataFrame with signals and individual condition checks
    """
    results = []
    
    for symbol, data in df.groupby("symbol"):
        data = data.sort_values(by="date").copy()
        
        # Check if indicators already exist in the data
        has_indicators = (
            'RSI' in data.columns and 
            'MA50' in data.columns and 
            'MACD' in data.columns and 
            'MACD_Signal' in data.columns and
            'Prev_Volume' in data.columns
        )
        
        if not has_indicators or data['RSI'].isna().all():
            # Indicators missing or all NaN - calculate them
            data = calculate_indicators(data)
        
        # Apply exact combination logic (Volume NOT used for signals)
        data = check_buy_conditions(
            data,
            rsi_threshold=rsi_threshold,
            ma_buffer=ma_buffer,
            volume_multiplier=volume_multiplier,
            enable_rsi=enable_rsi,
            enable_ma=enable_ma,
            enable_macd=enable_macd,
            enable_volume=enable_volume  # Passed but not used in signal logic
        )
        
        results.append(data)
    
    # Concatenate all symbols
    final_df = pd.concat(results).reset_index(drop=True)
    
    # Log summary
    buy_count = len(final_df[final_df['Recommendation'] == 'BUY'])
    reject_count = len(final_df) - buy_count
    
    # Show which indicators are active
    active_indicators = []
    if enable_ma:
        active_indicators.append(f"Step 1: Close >= MA50 × {1 + ma_buffer/100:.2f}")
    if enable_rsi:
        active_indicators.append(f"Step 2: RSI >= {rsi_threshold}")
    if enable_macd:
        active_indicators.append("Step 3: MACD > Signal")
    
    print(f"\n[INFO] Signal Generation Complete (Sequential Logic):")
    print(f"   - Sequential Steps: {' → '.join(active_indicators) if active_indicators else 'NONE (All disabled)'}")
    print(f"   - Volume NOT used for signals (only for quantity calculation)")
    print(f"   - BUY Signals: {buy_count}")
    print(f"   - REJECT Signals: {reject_count}")
    
    # Show sample BUY signals
    buy_signals = final_df[final_df['Recommendation'] == 'BUY']
    if len(buy_signals) > 0:
        print(f"\n[INFO] Sample BUY signals (Passed all 3 sequential steps):")
        for _, row in buy_signals.head(5).iterrows():
            print(f"   - {row['symbol']}: RSI={row['RSI']:.1f}, MA50={row['MA50']:.1f}, MACD={row['MACD']:.2f}")
    
    return final_df