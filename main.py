import datetime
import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt
from trading_logic import calculate_moving_averages, calculate_atr, calculate_adx, generate_signals
from backtester import Backtester

# List of Nasdaq-100 tickers (as of 2025)
nasdaq_100_tickers_current = [
    'AAPL', 'ABNB', 'ADBE', 'ADI', 'ADP', 'ADSK', 'AEP', 'AMAT', 'AMD', 'AMGN', 'AMZN', 'APP', 'ARM', 'ASML',
    'AVGO', 'AXON', 'AZN', 'BIIB', 'BKNG', 'BKR', 'CCEP', 'CDNS', 'CDW', 'CEG', 'CHTR', 'CMCSA', 'COST', 'CPRT',
    'CRWD', 'CSCO', 'CSGP', 'CSX', 'CTAS', 'CTSH', 'DASH', 'DDOG', 'DXCM', 'EA', 'EXC', 'FANG', 'FAST', 'FTNT',
    'GEHC', 'GFS', 'GILD', 'GOOG', 'GOOGL', 'HON', 'IDXX', 'INTC', 'INTU', 'ISRG', 'KDP', 'KHC', 'KLAC', 'LIN',
    'LRCX', 'LULU', 'MAR', 'MCHP', 'MDLZ', 'MELI', 'META', 'MNST', 'MRVL', 'MSFT', 'MSTR', 'MU', 'NFLX', 'NVDA',
    'NXPI', 'ODFL', 'ON', 'ORLY', 'PANW', 'PAYX', 'PCAR', 'PDD', 'PEP', 'PLTR', 'PYPL', 'QCOM', 'REGN', 'ROP',
    'ROST', 'SBUX', 'SHOP', 'SNPS', 'TEAM', 'TMUS', 'TRI', 'TSLA', 'TTD', 'TTWO', 'TXN', 'VRSK', 'VRTX', 'WBD',
    'WDAY', 'XEL', 'ZS'
]

FAST_WINDOW = 10
SLOW_WINDOW = 50
ATR_WINDOW = 14
ADX_WINDOW = 14
ADX_THRESHOLD = 25
INITIAL_CASH = 100000

def get_one_year_ticker_data_normal(tickers):
    # Use fixed dates for reproducible backtests
    end_date = '2024-01-01' # Set a fixed end date for consistency
    start_date = (pd.to_datetime(end_date) - pd.DateOffset(years=1)).strftime('%Y-%m-%d')
    
    print(f"Downloading data from {start_date} to {end_date}...")
    data = yf.download(tickers, start=start_date, end=end_date, progress=False, auto_adjust=True, timeout=60)
    return data

if __name__ == "__main__":
    DATA_FILE = 'nasdaq_data.parquet'
    
    try:
        # Try to load the data from the local file first
        data = pd.read_parquet(DATA_FILE)
        print(f"Loaded data from {DATA_FILE}")
    except FileNotFoundError:
        # If the file doesn't exist, download it and save it
        print(f"{DATA_FILE} not found. Downloading fresh data...")
        dataFrame_with_stock_info = get_one_year_ticker_data_normal(nasdaq_100_tickers_current)

        # Stack tickers into rows, flatten columns
        data = dataFrame_with_stock_info.stack(level=1, future_stack=True).reset_index()
        data.rename(columns={"level_1": "Ticker"}, inplace=True)
        data.to_parquet(DATA_FILE, index=False)
        print(f"Data saved to {DATA_FILE}")

    # --- Process Data and Generate Signals ---
    data['Date'] = pd.to_datetime(data['Date'])
    stacked_data = data.sort_values(by=['Date', 'Ticker']).set_index('Date')

    processed_ticker_dfs = []
    for ticker in stacked_data['Ticker'].unique():
        ticker_df = stacked_data[stacked_data['Ticker'] == ticker].copy()
        
        ticker_df = calculate_moving_averages(ticker_df, FAST_WINDOW, SLOW_WINDOW)
        ticker_df = calculate_atr(ticker_df, ATR_WINDOW)
        ticker_df = calculate_adx(ticker_df, ADX_WINDOW)
        ticker_df = generate_signals(ticker_df, ADX_THRESHOLD)
        
        processed_ticker_dfs.append(ticker_df)

    all_signals_df = pd.concat(processed_ticker_dfs)

    # --- Run Backtest ---
    # You can now control the selling behavior here.
    # Set prevent_loss_selling=True to avoid selling at a loss.
    # Set prevent_loss_selling=False to follow the original strategy.
    backtester = Backtester(initial_cash=INITIAL_CASH, prevent_loss_selling=False, allow_pyramiding=True) # Changed to allow pyramiding
    backtester.run(all_signals_df)

    # --- Report Results ---
    portfolio_history_df = pd.DataFrame(backtester.portfolio_history)
    final_portfolio_value = portfolio_history_df['value'].iloc[-1]

    print("\n--- Backtest Results ---")
    print(f"Initial Portfolio Value: ${backtester.initial_cash:,.2f}")
    print(f"Final Portfolio Value:   ${final_portfolio_value:,.2f}")
    
    profit = final_portfolio_value - backtester.initial_cash
    profit_percent = (profit / backtester.initial_cash) * 100
    
    print(f"Total Profit:            ${profit:,.2f} ({profit_percent:.2f}%)")
    print(f"Total Trades:            {len(backtester.trades)}")

    # --- Generate Graphs ---
    # 1. Portfolio Performance Graph
    portfolio_history_df.set_index('date', inplace=True)
    
    plt.figure(figsize=(12, 6))
    plt.plot(portfolio_history_df.index, portfolio_history_df['value'], label='Portfolio Value')
    plt.title('Portfolio Performance Over Time')
    plt.xlabel('Date')
    plt.ylabel('Portfolio Value ($)')
    plt.legend()
    plt.grid(True)
    plt.savefig('portfolio_performance.png')
    print("\nPortfolio performance graph saved to portfolio_performance.png")

    # 2. Individual Stock Chart (Example: AAPL)
    plt.figure(figsize=(12, 6))
    stock_to_plot = 'AAPL'
    aapl_df = all_signals_df[all_signals_df['Ticker'] == stock_to_plot].copy()
    
    plt.plot(aapl_df.index, aapl_df['Close'], label='Close Price', alpha=0.5)
    plt.plot(aapl_df.index, aapl_df['fast_mavg'], label=f'Fast MA ({FAST_WINDOW})', linestyle='--')
    plt.plot(aapl_df.index, aapl_df['slow_mavg'], label=f'Slow MA ({SLOW_WINDOW})', linestyle='--')
    
    buy_signals = aapl_df[aapl_df['signal'] == 'buy']
    sell_signals = aapl_df[aapl_df['signal'] == 'sell']
    
    plt.scatter(buy_signals.index, buy_signals['Close'], label='Buy Signal', marker='^', color='green', s=100)
    plt.scatter(sell_signals.index, sell_signals['Close'], label='Sell Signal', marker='v', color='red', s=100)
    
    plt.title(f'{stock_to_plot} Trading Signals')
    plt.xlabel('Date')
    plt.ylabel('Price ($)')
    plt.legend()
    plt.grid(True)
    plt.savefig(f'{stock_to_plot.lower()}_chart.png')
    print(f"Chart for {stock_to_plot} saved to {stock_to_plot.lower()}_chart.png")
