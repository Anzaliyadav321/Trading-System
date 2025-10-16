# signals/buy_signal.py
import pandas as pd
from backend.core.technical_indicators.technicals import calculate_indicators

def check_buy_conditions(data: pd.DataFrame) -> pd.DataFrame:
    """Apply PO's Buy conditions to stock data."""
    # Individual conditions
    data['RSI_OK'] = data['RSI'] >= 60
    data['MA_OK'] = data['close'] > data['MA50']
    data['MACD_OK'] = data['MACD'] > data['MACD_Signal']
    data['VOLUME_OK'] = data['volume'] >= 1.1 * data['Prev_Volume']

    # Final decision: all must be True
    data['Buy_Signal'] = data['RSI_OK'] & data['MA_OK'] & data['MACD_OK'] & data['VOLUME_OK']

    # Recommendation
    data['Recommendation'] = data['Buy_Signal'].apply(lambda x: "BUY" if x else "REJECT")

    return data


def generate_buy_signals(df: pd.DataFrame) -> pd.DataFrame:
    """
    Process all symbols and return DataFrame with Buy/Reject signals.
    Keeps individual conditions for audit/debug.
    """
    results = []
    for symbol, data in df.groupby("symbol"):
        data = data.sort_values(by="date").copy()

        # Calculate technical indicators first
        data = calculate_indicators(data)

        # Apply buy/reject logic
        data = check_buy_conditions(data)

        results.append(data)

    # Concatenate all symbols
    return pd.concat(results).reset_index(drop=True)
