
import pandas as pd

class Backtester:
    def __init__(self, initial_cash, amount_to_buy=10):
        self.initial_cash = initial_cash
        self.cash = initial_cash
        self.positions = {}
        self.trades = []
        self.amount_to_buy = amount_to_buy

    def run(self, data):
        """Runs the backtest on the given data."""
        for index, row in data.iterrows():
            if pd.notna(row['Close']):
                ticker = row['Ticker']
                if row['signal'] == 'buy' and self.cash > row['Close']:
                    # Simple case: buy ten shares
                    self.positions[ticker] = self.positions.get(ticker, 0) + self.amount_to_buy
                    self.cash -= row['Close'] * self.amount_to_buy
                    self.trades.append({'date': index, 'ticker': ticker, 'action': 'buy', 'price': row['Close']})
                elif row['signal'] == 'sell' and self.positions.get(ticker, 0) > 0:
                    # Simple case: sell ten shares
                    self.positions[ticker] -= self.amount_to_buy
                    self.cash += row['Close'] * self.amount_to_buy
                    self.trades.append({'date': index, 'ticker': ticker, 'action': 'sell', 'price': row['Close']})

    def get_portfolio_value(self, current_prices):
        """Calculates the current total value of the portfolio."""
        value = self.cash
        for ticker, quantity in self.positions.items():
            value += quantity * current_prices.get(ticker, 0)
        return value
