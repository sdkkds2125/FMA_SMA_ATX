# FMA SMA ATX Trading Strategy

This project implements a trading strategy based on the Fast Moving Average (FMA), Slow Moving Average (SMA), and Average Directional Index (ADX).

## Strategy

The trading strategy is as follows:

*   **Buy Signal:** When the Fast Moving Average crosses above the Slow Moving Average and the ADX is above a certain threshold, a buy signal is generated.
*   **Sell Signal:** When the Fast Moving Average crosses below the Slow Moving Average and the ADX is above a certain threshold, a sell signal is generated.

The ADX is used as a filter to ensure that the trading signals are only generated when the market is trending.

## How to Use

To use this project, you will need to have Python 3 installed. You will also need to install the following libraries:

*   pandas
*   yfinance

You can install these libraries using pip:

```
pip install pandas yfinance
```

Once you have installed the required libraries, you can run the project by executing the `main.py` file:

```
python main.py
```

The project will then download the latest stock data for the Nasdaq-100, calculate the trading signals, and run a backtest. The backtest results will be printed to the console.

## Backtester

The `backtester.py` file contains a `Backtester` class that can be used to backtest a trading strategy. The `Backtester` class takes an initial cash amount and the amount to buy for each trade as input. It then runs the backtest and returns the final portfolio value.

## Trading Logic

The `trading_logic.py` file contains the functions that are used to calculate the moving averages, ATR, and ADX. It also contains the function that is used to generate the trading signals.
