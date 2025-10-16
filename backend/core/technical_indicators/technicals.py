# backend/core/technical_indicators/technicals.py
import pandas as pd
import ta

def calculate_indicators(data: pd.DataFrame) -> pd.DataFrame:
    """Add RSI, MA50, MACD, MACD Signal, and Prev_Volume to stock data."""
    data['RSI'] = ta.momentum.RSIIndicator(data['close'], window=14).rsi()
    data['MA50'] = data['close'].rolling(window=50).mean()

    macd = ta.trend.MACD(data['close'])
    data['MACD'] = macd.macd()
    data['MACD_Signal'] = macd.macd_signal()

    data['Prev_Volume'] = data['volume'].shift(1)

    return data
