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

# # backend/core/pipeline/nepse_pipeline.py

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
    """Merge daily CSV into master and update indicators"""
    master_df = pd.read_csv(MASTER_PATH)
    master_df['date'] = pd.to_datetime(master_df['date'])

    daily_df = pd.read_csv(DAILY_PATH)
    daily_df['date'] = pd.to_datetime(daily_df['date'])

    combined = pd.concat([master_df, daily_df], ignore_index=True)
    combined = combined.drop_duplicates(subset=["symbol", "date"])
    combined = combined.sort_values(by=["symbol", "date"]).reset_index(drop=True)

    combined = calculate_indicators(combined)
    combined.to_csv(MASTER_PATH, index=False)
    return combined

def run_pipeline():
    """Run pipeline → update master, generate signals for latest date only."""
    df = update_master_with_daily()

    # 🟢 Keep only the latest available trading date
    df['date'] = pd.to_datetime(df['date'])
    latest_date = df['date'].max()
    df_latest = df[df['date'] == latest_date]

    print(f"[INFO] Running pipeline for latest date: {latest_date.date()} with {len(df_latest)} rows")

    # Generate signals only for today's data
    final_df = generate_buy_signals(df_latest)
    final_df = final_df.sort_values(by=["date", "symbol"]).reset_index(drop=True)

    final_df.to_csv(ALL_SIGNALS_PATH, index=False)

    buy_signals = final_df[final_df['Recommendation'] == "BUY"]
    buy_signals.to_csv(BUY_SIGNALS_PATH, index=False)

    print(f"[INFO] Generated {len(buy_signals)} BUY signals for {latest_date.date()}")
    return final_df, buy_signals


def get_today_signals():
    """Return only today's signals (BUY + REJECT)."""
    final_df, _ = run_pipeline()

    # Convert to date objects only (ignore hours/min/sec)
    final_df['date'] = pd.to_datetime(final_df['date']).dt.date
    today = date.today()

    today_signals = final_df[final_df['date'] == today]

    print(f"[INFO] Found {len(today_signals)} signals for {today}")
    return today_signals.to_dict(orient="records")

