import datetime
import yfinance as yf
import pandas as pd
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
    today = datetime.datetime.now()
    year_ago = today - datetime.timedelta(days=365)
    data = yf.download(tickers, start=year_ago, end=today, progress=False, auto_adjust=True)
    return data

if __name__ == "__main__":
    dataFrame_with_stock_info = get_one_year_ticker_data_normal(nasdaq_100_tickers_current)

    # Stack tickers into rows, flatten columns
    stacked = dataFrame_with_stock_info.stack(level=1, future_stack=True).reset_index()
    stacked.rename(columns={"level_1": "Ticker"}, inplace=True)
    
    # Save the clean, stacked data to CSV and Parquet
    todays_date = str(datetime.date.today())
    stacked.to_csv("Nasdaq100Prices{0}.csv".format(todays_date), index=False)
    stacked.to_parquet('nasdaq_data.parquet', index=False)

    # --- Process Data and Generate Signals ---
    data = pd.read_parquet('nasdaq_data.parquet')
    data['Date'] = pd.to_datetime(data['Date'])
    stacked_data = data.sort_values(by=['Date', 'Ticker']).set_index('Date')

    all_signals_df = pd.DataFrame()
    for ticker in stacked_data['Ticker'].unique():
        ticker_df = stacked_data[stacked_data['Ticker'] == ticker].copy()
        
        ticker_df = calculate_moving_averages(ticker_df, FAST_WINDOW, SLOW_WINDOW)
        ticker_df = calculate_atr(ticker_df, ATR_WINDOW)
        ticker_df = calculate_adx(ticker_df, ADX_WINDOW)
        ticker_df = generate_signals(ticker_df, ADX_THRESHOLD)
        
        all_signals_df = pd.concat([all_signals_df, ticker_df])

    # --- Run Backtest ---
    backtester = Backtester(initial_cash=INITIAL_CASH)
    backtester.run(all_signals_df)

    # --- Report Results ---
    last_day = all_signals_df.index.max()
    last_day_prices = all_signals_df[all_signals_df.index == last_day].set_index('Ticker')['Close'].to_dict()
    
    final_portfolio_value = backtester.get_portfolio_value(last_day_prices)

    print("\n--- Backtest Results ---")
    print(f"Initial Portfolio Value: ${backtester.initial_cash:,.2f}")
    print(f"Final Portfolio Value:   ${final_portfolio_value:,.2f}")
    
    profit = final_portfolio_value - backtester.initial_cash
    profit_percent = (profit / backtester.initial_cash) * 100
    
    print(f"Total Profit:            ${profit:,.2f} ({profit_percent:.2f}%)")
    print(f"Total Trades:            {len(backtester.trades)}")
