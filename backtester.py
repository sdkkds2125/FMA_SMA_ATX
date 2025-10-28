import pandas as pd

class Backtester:
    def __init__(self, initial_cash, trade_size_usd=10000, prevent_loss_selling=False, allow_pyramiding=False):
        self.initial_cash = initial_cash
        self.cash = initial_cash
        self.positions = {} # Will now store {'ticker': {'quantity': X, 'average_purchase_price': Y}}
        self.trades = []
        self.last_trade_date = {} # Tracks the last trade date for each ticker to prevent daily pyramiding
        self.trade_size_usd = trade_size_usd
        self.prevent_loss_selling = prevent_loss_selling
        self.allow_pyramiding = allow_pyramiding
        self.portfolio_history = [] # To store daily portfolio value

    def run(self, data):
        """Runs the backtest on the given data, processing day by day."""
        # Ensure data is sorted by date
        data = data.sort_index()
        
        # Get all unique dates from the data's index
        for date in data.index.unique():
            # Get all the market data for the current day
            daily_data = data.loc[date]

            # CRITICAL FIX: Ensure daily_data is always a DataFrame, even if only one row is returned.
            # This must happen before any other operations on daily_data.
            if isinstance(daily_data, pd.Series):
                daily_data = daily_data.to_frame().T

            # --- Start of Day --- 
            current_prices = daily_data.set_index('Ticker')['Close'].to_dict()

            # If all prices for the day are NaN or the price dict is empty, it's an incomplete day.
            if not current_prices or all(pd.isna(p) for p in current_prices.values()):
                continue
            
            # --- Trading Logic: Execute trades for the day FIRST ---
            for index, row in daily_data.iterrows():
                ticker = row['Ticker']
                price = row['Close']
                
                if pd.isna(price):
                    continue # Skip if price is not available

                # --- Improved Trading Logic ---
                # On a buy signal, decide whether to open a new position or add to an existing one.
                if row['signal'] == 'buy' and self.cash >= self.trade_size_usd:
                    quantity_to_buy = self.trade_size_usd / price

                    if ticker not in self.positions: # Open a new position
                        self.positions[ticker] = {'quantity': quantity_to_buy, 'average_purchase_price': price}
                        self.cash -= self.trade_size_usd
                        self.trades.append({'date': date, 'ticker': ticker, 'action': 'buy', 'price': price, 'quantity': quantity_to_buy})
                    elif self.allow_pyramiding: # Add to an existing position
                        current_quantity = self.positions[ticker]['quantity']
                        current_avg_price = self.positions[ticker]['average_purchase_price']
                        
                        new_total_quantity = current_quantity + quantity_to_buy
                        new_avg_price = ((current_quantity * current_avg_price) + (quantity_to_buy * price)) / new_total_quantity
                        
                        self.positions[ticker]['quantity'] = new_total_quantity
                        self.positions[ticker]['average_purchase_price'] = new_avg_price
                        self.cash -= self.trade_size_usd
                        
                        # Update the last trade date to prevent buying again tomorrow
                        self.last_trade_date[ticker] = date
                        
                        self.trades.append({'date': date, 'ticker': ticker, 'action': 'buy_add', 'price': price, 'quantity': quantity_to_buy})
                
                # On a sell signal, if we have a position, sell all of it.
                elif row['signal'] == 'sell' and ticker in self.positions:
                    # If prevent_loss_selling is True, only sell if it's a profitable trade.
                    if self.prevent_loss_selling and price < self.positions[ticker]['average_purchase_price']:
                        # Skip the sale, it's a loss
                        continue
                    else:
                        # Proceed with the sale
                        position_data = self.positions.pop(ticker) # Remove position and get data
                        quantity_to_sell = position_data['quantity']
                        self.cash += price * quantity_to_sell
                        self.trades.append({'date': date, 'ticker': ticker, 'action': 'sell', 'price': price, 'quantity': quantity_to_sell})
            
            # --- End of Day Valuation: Calculate portfolio value AFTER trades ---
            stock_value = 0
            for ticker, position_data in self.positions.items():
                # Use the day's closing price for valuation of the current quantity
                if ticker in current_prices and pd.notna(current_prices.get(ticker)):
                    stock_value += position_data['quantity'] * current_prices[ticker]

            total_value = self.cash + stock_value
            self.portfolio_history.append({'date': date, 'value': total_value})
