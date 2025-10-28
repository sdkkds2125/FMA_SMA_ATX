import pandas as pd
import numpy as np

def calculate_moving_averages(df, fast_window, slow_window):
    """Calculates fast and slow moving averages for a given DataFrame."""
    df['fast_mavg'] = df['Close'].rolling(window=fast_window, min_periods=1).mean()
    df['slow_mavg'] = df['Close'].rolling(window=slow_window, min_periods=1).mean()
    return df

def calculate_atr(df, window):
    """Calculates the Average True Range (ATR) for a given DataFrame."""
    df['high_low'] = df['High'] - df['Low']
    df['high_close'] = (df['High'] - df['Close'].shift()).abs()
    df['low_close'] = (df['Low'] - df['Close'].shift()).abs()
    df['tr'] = df[['high_low', 'high_close', 'low_close']].max(axis=1)
    # Use an exponential moving average (Wilder's Smoothing) for a standard ATR calculation
    df['atr'] = df['tr'].ewm(alpha=1/window, adjust=False).mean()
    return df

def calculate_adx(df, window):
    """Calculates the Average Directional Index (ADX) for a given DataFrame."""
    # Calculate Directional Movement
    df['move_up'] = df['High'].diff()
    df['move_down'] = -df['Low'].diff()
    
    df['plus_dm'] = df.apply(lambda row: row['move_up'] if row['move_up'] > row['move_down'] and row['move_up'] > 0 else 0, axis=1)
    df['minus_dm'] = df.apply(lambda row: row['move_down'] if row['move_down'] > row['move_up'] and row['move_down'] > 0 else 0, axis=1)

    # Use Exponential Moving Average (Wilder's Smoothing) for standard ADX calculation
    df['plus_di'] = 100 * (df['plus_dm'].ewm(alpha=1/window, min_periods=window).mean() / df['atr'])
    df['minus_di'] = 100 * (df['minus_dm'].ewm(alpha=1/window, min_periods=window).mean() / df['atr'])
    
    # Calculate the Directional Index (DX)
    df['dx'] = (abs(df['plus_di'] - df['minus_di']) / (df['plus_di'] + df['minus_di']).abs()).fillna(0) * 100
    # Calculate the ADX
    df['adx'] = df['dx'].ewm(alpha=1/window, min_periods=window).mean()
    return df

def generate_signals(df, adx_threshold):
    """Generates trading signals based on moving average crossover and ADX filter."""
    # Define conditions for a clear state machine
    # 1. Buy State: Fast MA is above Slow MA AND the trend is strong (ADX > threshold)
    buy_condition = (df['fast_mavg'] > df['slow_mavg']) & (df['adx'] > adx_threshold)
    
    # 2. Sell State: Fast MA crosses below Slow MA. This is our exit signal.
    sell_condition = (df['fast_mavg'] < df['slow_mavg'])

    # Use np.select for a clean, non-overlapping assignment of signals.
    # This prevents signals from being accidentally overwritten.
    # The order matters: we check for buy, then sell, otherwise it's a hold.
    conditions = [buy_condition, sell_condition]
    choices = ['buy', 'sell']
    df['signal'] = np.select(conditions, choices, default='hold')
    
    return df
