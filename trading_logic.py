import pandas as pd

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
    df['atr'] = df['tr'].rolling(window=window, min_periods=1).mean()
    return df

def calculate_adx(df, window):
    """Calculates the Average Directional Index (ADX) for a given DataFrame."""
    df['plus_dm'] = (df['High'] - df['High'].shift()).apply(lambda x: x if x > 0 else 0)
    df['minus_dm'] = (df['Low'].shift() - df['Low']).apply(lambda x: x if x > 0 else 0)
    
    df['plus_di'] = 100 * (df['plus_dm'].rolling(window=window).sum() / df['atr'])
    df['minus_di'] = 100 * (df['minus_dm'].rolling(window=window).sum() / df['atr'])
    
    df['dx'] = 100 * (abs(df['plus_di'] - df['minus_di']) / (df['plus_di'] + df['minus_di']))
    df['adx'] = df['dx'].rolling(window=window).mean()
    return df

def generate_signals(df, adx_threshold):
    """Generates trading signals based on moving average crossover and ADX filter."""
    df['signal'] = 'hold'
    df.loc[(df['fast_mavg'] > df['slow_mavg']) & (df['fast_mavg'].shift() < df['slow_mavg'].shift()) & (df['adx'] > adx_threshold), 'signal'] = 'buy'
    df.loc[(df['fast_mavg'] < df['slow_mavg']) & (df['fast_mavg'].shift() > df['slow_mavg'].shift()) & (df['adx'] > adx_threshold), 'signal'] = 'sell'
    return df
