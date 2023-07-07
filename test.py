import os
import shutil
import pytz
import requests
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import mplfinance as mpf
import pandas as pd
import talib


def check_rsi(df):
    df['rsi'] = talib.RSI(df['Close'])
    df['overbought'] = df['rsi'] > 70
    df['oversold'] = df['rsi'] < 30
    return df


def check_macd_trend(df):
    df['macd'], _, _ = talib.MACD(df['Close'])
    df['macd_trend'] = df['macd'].diff() > 0
    return df

# def check_macd_crossover(df):
#     df['macd'], df['macd_signal'], _ = talib.MACD(df['Close'])
#     df['macd_crossover'] = ((df['macd'] > df['macd_signal']) & (df['macd'].shift() <= df['macd_signal'].shift()))
#     return df


def check_macd_crossover(df):
    df['macd'], df['macd_signal'], _ = talib.MACD(df['Close'])
    df['macd_crossover'] = ((df['macd'] > df['macd_signal']) & (
        df['macd'].shift() <= df['macd_signal'].shift()))
    df['macd_crossover_up'] = ((df['macd'] > df['macd_signal']) & (
        df['macd'].shift() <= df['macd_signal'].shift()))
    df['macd_crossover_down'] = ((df['macd'] < df['macd_signal']) & (
        df['macd'].shift() >= df['macd_signal'].shift()))
    return df

# resolution	string	Chart resolution (1, 5, 15, 60, 240, 1D)
timeFrame = "60"
# symbols  = ["BTC", "ETH", "KUB", "OP", "APE", "BNB","DOGE", "XRP", "ADA", "IOST", "MANA"]

def get_symbols():
    symbols = []
    res = requests.request("GET", "https://api.bitkub.com/api/market/ticker")
    data = res.json()
    for symbol in data:
        symbols.append(str(symbol.replace("THB_", "")).strip())
    
    return symbols

if __name__ == "__main__":
    symbols = get_symbols()
    print(symbols)
    for symbol in symbols:
        dte = datetime.now()
        fromDte = int((dte - timedelta(hours=100)).strftime("%s"))
        toDte = int(dte.strftime("%s"))

        url = f"https://api.bitkub.com/tradingview/history?symbol={symbol}_THB&resolution={timeFrame}&from={fromDte}&to={toDte}"
        res = requests.request("GET", url)
        obj = res.json()

        klines = []
        x = len(obj["c"])
        for i in range(x):
            klines.append([obj['t'][i],obj['o'][i],obj['c'][i],obj['h'][i],obj['l'][i],obj['v'][i]])

        df = pd.DataFrame(klines, columns=['Date', 'Open', 'Close', 'High', 'Low', 'Volume'])
        df['Date'] = df['Date'].astype(float)
        df['Open'] = df['Open'].astype(float)
        df['Close'] = df['Close'].astype(float)
        df['High'] = df['High'].astype(float)
        df['Low'] = df['Low'].astype(float)
        df['Volume'] = df['Volume'].astype(float)

        # Convert the 'Date' column to datetime format
        try:
            df['Date'] = pd.to_datetime(df['Date'] * 1000, unit='ms')
        except ValueError:
            df['Date'] = pd.to_datetime(df['Date'] * 1000, unit='s')

        # Set the timezone for the 'Date' column
        timezone = 'Asia/Bangkok'
        df['Date'] = df['Date'].dt.tz_localize(
            pytz.utc).dt.tz_convert(timezone)
        # # Format datetime column as desired (e.g., 'YYYY-MM-DD HH:MM:SS')
        # df['Date'] = df['Date'].dt.strftime('%Y-%m-%d %H:%M:%S')
        df.set_index('Date', inplace=True)
        df = check_macd_crossover(df)
        df = check_macd_trend(df)
        df = check_rsi(df)


        ## Create Folder
        try:
            shutil.rmtree(f"export/{symbol}")
        except:
            pass
        try:
            os.makedirs(f"export/{symbol}")
        except:
            pass

        df.to_csv(f'export/{symbol}/{symbol}.csv')
        # # Sort the DataFrame by the date column
        # df = df.iloc[::-1]
        # Calculate MACD values
        ema_12 = df['Close'].ewm(span=12, adjust=False).mean()
        ema_26 = df['Close'].ewm(span=26, adjust=False).mean()
        ema_99 = df['Close'].ewm(span=99, adjust=False).mean()
        # Plot the candlestick chart with EMA lines
        fig, ax = mpf.plot(df, type='candle', style='binance', 
                           addplot=[
                               mpf.make_addplot(ema_12, color='blue'),
                               mpf.make_addplot(ema_26, color='red'),
                               mpf.make_addplot(ema_99, color='yellow')
                            ], returnfig=True)
        candlePath = f"export/{symbol}/{symbol}_CANDLESTICK.png"
        plt.savefig(candlePath)