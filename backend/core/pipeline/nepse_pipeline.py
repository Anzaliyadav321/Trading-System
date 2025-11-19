# # backend/core/pipeline/nepse_pipeline.py
# import pandas as pd
# from pathlib import Path
# from backend.core.signals.buy_signals import generate_buy_signals
# from backend.core.technical_indicators.technicals import calculate_indicators

# # File paths (relative to backend/core/data)
# DATA_DIR = Path(__file__).resolve().parent.parent / "data"
# MASTER_PATH = DATA_DIR / "master_data.csv"
# DAILY_PATH = DATA_DIR / "MeroLagani_Daily.csv"
# ALL_SIGNALS_PATH = DATA_DIR / "all_signals.csv"
# BUY_SIGNALS_PATH = DATA_DIR / "buy_signals.csv"


# def update_master_with_daily():
#     """Read daily CSV, append to master CSV, recalc indicators, and save updated master CSV."""
#     master_df = pd.read_csv(MASTER_PATH)
#     master_df['date'] = pd.to_datetime(master_df['date'])

#     daily_df = pd.read_csv(DAILY_PATH)
#     daily_df['date'] = pd.to_datetime(daily_df['date'])

#     combined = pd.concat([master_df, daily_df], ignore_index=True)
#     combined = combined.drop_duplicates(subset=["symbol", "date"])
#     combined = combined.sort_values(by=["symbol", "date"]).reset_index(drop=True)

#     # Recalculate technical indicators
#     combined = calculate_indicators(combined)

#     combined.to_csv(MASTER_PATH, index=False)
#     print("Master data updated successfully with technical indicators.")
#     return combined


# def run_pipeline():
#     """Run the full NEPSE signal pipeline and save outputs."""
#     print("Running NEPSE Buy Signal Pipeline...")

#     # Step 1: Update master with new daily data
#     df = update_master_with_daily()

#     # Step 2: Generate signals (BUY + REJECT)
#     final_df = generate_buy_signals(df)
#     final_df = final_df.sort_values(by=["date", "symbol"]).reset_index(drop=True)

#     # Step 3: Save all signals (BUY + REJECT)
#     final_df.to_csv(ALL_SIGNALS_PATH, index=False)
#     print(f"All signals saved to {ALL_SIGNALS_PATH}")

#     # Step 4: Save only BUY signals
#     buy_signals = final_df[final_df['Recommendation'] == "BUY"]
#     buy_signals.to_csv(BUY_SIGNALS_PATH, index=False)
#     print(f"Buy signals saved to {BUY_SIGNALS_PATH}")

#     return final_df, buy_signals


# if __name__ == "__main__":
#     final_df, buy_signals = run_pipeline()

#     # Step 5: Print last 15 signals for quick check
#     print("\nLast 15 signals:")
#     print(final_df[['date','symbol','close','RSI','MA50','MACD','MACD_Signal',
#                     'volume','RSI_OK','MA_OK','MACD_OK','VOLUME_OK','Recommendation']].tail(15))

#     print("Pipeline finished successfully.")

# # # backend/core/pipeline/nepse_pipeline.py

# import pandas as pd
# from pathlib import Path
# from datetime import date
# from backend.core.signals.buy_signals import generate_buy_signals
# from backend.core.technical_indicators.technicals import calculate_indicators

# # Paths
# DATA_DIR = Path(__file__).resolve().parent.parent / "data"
# MASTER_PATH = DATA_DIR / "Master_data.csv"
# DAILY_PATH = DATA_DIR / "MeroLagani_Daily.csv"
# ALL_SIGNALS_PATH = DATA_DIR / "all_signals.csv"
# BUY_SIGNALS_PATH = DATA_DIR / "buy_signals.csv"


# def update_master_with_daily():
#     """Merge daily CSV into master and update indicators"""
#     master_df = pd.read_csv(MASTER_PATH)
#     master_df['date'] = pd.to_datetime(master_df['date'])

#     daily_df = pd.read_csv(DAILY_PATH)
#     daily_df['date'] = pd.to_datetime(daily_df['date'])

#     combined = pd.concat([master_df, daily_df], ignore_index=True)
#     combined = combined.drop_duplicates(subset=["symbol", "date"])
#     combined = combined.sort_values(by=["symbol", "date"]).reset_index(drop=True)

#     combined = calculate_indicators(combined)
#     combined.to_csv(MASTER_PATH, index=False)
#     return combined

# def run_pipeline():
#     """Run pipeline → update master, generate signals for latest date only."""
#     df = update_master_with_daily()

#     # Keep only the latest available trading date
#     df['date'] = pd.to_datetime(df['date'])
#     latest_date = df['date'].max()
#     df_latest = df[df['date'] == latest_date]

#     print(f"[INFO] Running pipeline for latest date: {latest_date.date()} with {len(df_latest)} rows")

#     # Generate signals only for today's data
#     final_df = generate_buy_signals(df_latest)
#     final_df = final_df.sort_values(by=["date", "symbol"]).reset_index(drop=True)

#     final_df.to_csv(ALL_SIGNALS_PATH, index=False)

#     buy_signals = final_df[final_df['Recommendation'] == "BUY"]
#     buy_signals.to_csv(BUY_SIGNALS_PATH, index=False)

#     print(f"[INFO] Generated {len(buy_signals)} BUY signals for {latest_date.date()}")
#     return final_df, buy_signals


# def get_today_signals():
#     """Return only today's signals (BUY + REJECT)."""
#     final_df, _ = run_pipeline()

#     # Convert to date objects only (ignore hours/min/sec)
#     final_df['date'] = pd.to_datetime(final_df['date']).dt.date
#     today = date.today()

#     today_signals = final_df[final_df['date'] == today]

#     print(f"[INFO] Found {len(today_signals)} signals for {today}")
#     return today_signals.to_dict(orient="records")


# backend/core/pipeline/nepse_pipeline.py

import pandas as pd
from pathlib import Path
from datetime import date
from backend.core.signals.buy_signals import generate_buy_signals
from backend.core.technical_indicators.technicals import calculate_indicators

# Paths
DATA_DIR = Path(__file__).resolve().parent.parent / "data"
MASTER_PATH = DATA_DIR / "Master_data.csv"
DAILY_PATH = DATA_DIR / "MeroLagani_Daily.csv"
ALL_SIGNALS_PATH = DATA_DIR / "all_signals.csv"
BUY_SIGNALS_PATH = DATA_DIR / "buy_signals.csv"


def update_master_with_daily():
    """
    Merge daily CSV into master and update indicators.
    Handles case where daily file doesn't exist or is empty.
    """
    print("[INFO] Loading master data...")
    master_df = pd.read_csv(MASTER_PATH)
    master_df['date'] = pd.to_datetime(master_df['date'])

    # Check if daily file exists
    if not DAILY_PATH.exists():
        print(f"[WARNING] Daily file not found: {DAILY_PATH}")
        print("[WARNING] Creating empty daily file for future use...")
        
        # Create empty daily file with correct schema
        empty_daily = pd.DataFrame(columns=[
            'date', 'symbol', 'open', 'high', 'low', 'close', 
            'volume', 'change_percent', 'source', 'timestamp'
        ])
        empty_daily.to_csv(DAILY_PATH, index=False)
        print(f"[INFO] ✅ Empty daily file created at {DAILY_PATH}")
        
        # Return master as-is (no new data to merge)
        print("[INFO] No new data to merge - using existing master data")
        print("[INFO] Indicators already calculated in master data")
        return master_df

    print("[INFO] Loading daily scraped data...")
    daily_df = pd.read_csv(DAILY_PATH)
    
    # Check if daily file is empty
    if len(daily_df) == 0:
        print("[WARNING] Daily file is empty - no new data to merge")
        print("[INFO] Using existing master data")
        return master_df
    
    daily_df['date'] = pd.to_datetime(daily_df['date'])

    print(f"[INFO] Master has {len(master_df)} rows, Daily has {len(daily_df)} rows")

    # Combine and remove duplicates
    combined = pd.concat([master_df, daily_df], ignore_index=True)
    combined = combined.drop_duplicates(subset=["symbol", "date"], keep='last')
    combined = combined.sort_values(by=["symbol", "date"]).reset_index(drop=True)

    print(f"[INFO] Combined data has {len(combined)} rows")
    print("[INFO] Calculating technical indicators...")

    # Calculate indicators for all data
    combined = calculate_indicators(combined)

    # Save updated master
    combined.to_csv(MASTER_PATH, index=False)
    print(f"[INFO] ✅ Updated master data saved to {MASTER_PATH}")

    return combined


def run_pipeline(
    enable_rsi: bool = True,
    enable_ma: bool = True,
    enable_macd: bool = True,
    enable_volume: bool = True
):
    """
    Run FULL pipeline with configurable indicators.
    
    PO's rules are FIXED:
    - RSI >= 60 (FIXED threshold)
    - Close > MA50 (FIXED threshold)
    - MACD > MACD_Signal (FIXED rule)
    - Volume >= 1.1 × Prev_Volume (FIXED threshold)
    
    What's configurable:
    - Which indicators to CHECK (enable/disable from sidebar)
    
    This MODIFIES master_data.csv - only call from scheduler!
    
    Args:
        enable_rsi: Check RSI >= 60 condition (default: True)
        enable_ma: Check Close > MA50 condition (default: True)
        enable_macd: Check MACD > Signal condition (default: True)
        enable_volume: Check Volume >= 1.1× Prev condition (default: True)
    
    Returns:
        tuple: (final_df, buy_signals) - DataFrames with all signals and buy signals
    """
    print("\n" + "="*80)
    print("STARTING FULL PIPELINE")
    print("="*80)
    
    # Step 1: Update master data with today's scrape
    df = update_master_with_daily()

    # Step 2: Get only the latest trading date
    df['date'] = pd.to_datetime(df['date'])
    latest_date = df['date'].max()
    df_latest = df[df['date'] == latest_date]

    print(f"\n[INFO] Processing signals for latest date: {latest_date.date()}")
    print(f"[INFO] Total stocks on this date: {len(df_latest)}")

    # Step 3: Generate buy signals with indicator toggles
    print("[INFO] Generating buy signals with PO's fixed rules...")
    
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
    
    print(f"[INFO] Active checks: {', '.join(active_indicators) if active_indicators else 'NONE'}")
    
    final_df = generate_buy_signals(
        df_latest,
        enable_rsi=enable_rsi,
        enable_ma=enable_ma,
        enable_macd=enable_macd,
        enable_volume=enable_volume
    )
    final_df = final_df.sort_values(by=["date", "symbol"]).reset_index(drop=True)

    # Step 4: Save all signals
    final_df.to_csv(ALL_SIGNALS_PATH, index=False)
    print(f"[INFO] ✅ Saved all signals to: {ALL_SIGNALS_PATH}")

    # Step 5: Filter and save BUY signals only
    buy_signals = final_df[final_df['Recommendation'] == "BUY"]
    buy_signals.to_csv(BUY_SIGNALS_PATH, index=False)
    
    print(f"\n[INFO] Pipeline Results:")
    print(f"   - Date: {latest_date.date()}")
    print(f"   - Total signals: {len(final_df)}")
    print(f"   - BUY signals: {len(buy_signals)}")
    reject_df = final_df[final_df['Recommendation'].str.startswith('REJECT')]
    print(f"   - REJECT signals: {len(reject_df)}")
    print("="*80 + "\n")

    return final_df, buy_signals


def get_today_signals():
    """
    Return today's signals (BUY + REJECT) from SAVED CSV file.
    
    This is READ-ONLY - doesn't regenerate signals.
    Returns cached results from last pipeline run.
    
    If you need fresh signals, call run_pipeline() first.
    
    Returns:
        list: List of dictionaries with signal data for today
    """
    # Check if signals file exists
    if not ALL_SIGNALS_PATH.exists():
        print(f"[WARNING] Signals file not found: {ALL_SIGNALS_PATH}")
        print("[WARNING] Run pipeline first to generate signals")
        return []
    
    # Read from saved all_signals.csv (generated by scheduler)
    final_df = pd.read_csv(ALL_SIGNALS_PATH)
    
    # Convert to date objects only (ignore hours/min/sec)
    final_df['date'] = pd.to_datetime(final_df['date']).dt.date
    today = date.today()

    # Filter for today's signals
    today_signals = final_df[final_df['date'] == today]

    print(f"[INFO] Loaded {len(today_signals)} signals for {today}")
    
    if len(today_signals) == 0:
        print(f"[WARNING] No signals found for today ({today})")
        print(f"[WARNING] Latest date in file: {final_df['date'].max()}")
    
    return today_signals.to_dict(orient="records")


def get_signals_by_date(target_date):
    """
    Get signals for a specific date from saved CSV.
    
    Args:
        target_date: date object or string (YYYY-MM-DD)
    
    Returns:
        list: List of dictionaries with signal data for specified date
    """
    if not ALL_SIGNALS_PATH.exists():
        print(f"[WARNING] Signals file not found: {ALL_SIGNALS_PATH}")
        return []
    
    final_df = pd.read_csv(ALL_SIGNALS_PATH)
    final_df['date'] = pd.to_datetime(final_df['date']).dt.date
    
    # Convert target_date to date object if string
    if isinstance(target_date, str):
        target_date = pd.to_datetime(target_date).date()
    
    # Filter for specified date
    date_signals = final_df[final_df['date'] == target_date]
    
    print(f"[INFO] Found {len(date_signals)} signals for {target_date}")
    return date_signals.to_dict(orient="records")


def get_last_n_days_signals(days=14):
    """
    Get signals for last N days from saved CSV.
    
    Args:
        days: Number of days to retrieve (default: 14)
    
    Returns:
        pandas.DataFrame: DataFrame with signals from last N days
    """
    if not ALL_SIGNALS_PATH.exists():
        print(f"[WARNING] Signals file not found: {ALL_SIGNALS_PATH}")
        return pd.DataFrame()
    
    final_df = pd.read_csv(ALL_SIGNALS_PATH)
    final_df['date'] = pd.to_datetime(final_df['date'])
    
    # Get cutoff date
    latest_date = final_df['date'].max()
    cutoff_date = latest_date - pd.Timedelta(days=days)
    
    # Filter last N days
    recent_signals = final_df[final_df['date'] >= cutoff_date]
    recent_signals = recent_signals.sort_values('date', ascending=False)
    
    print(f"[INFO] Loaded {len(recent_signals)} signals from last {days} days")
    print(f"[INFO] Date range: {recent_signals['date'].min().date()} to {recent_signals['date'].max().date()}")
    
    return recent_signals
