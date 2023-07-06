import os
import shutil
from kucoin.client import Market
import matplotlib.pyplot as plt
import mplfinance as mpf
import pandas as pd
import pytz
import talib
import requests

client = Market(url='https://openapi-v2.kucoin.com')


def send_line_notification(message, image_path):
    line_token = 'BfTqtBO0kuo5mqneTdBoe5ktUAnxYrHIoaWhLRcBTwj'
    url = 'https://notify-api.line.me/api/notify'
    headers = {'Authorization': f'Bearer {line_token}'}
    payload = {
        "message": message
    }
    if image_path:
        files = {
            "imageFile": open(image_path, "rb")
        }
        response = requests.post(url, headers=headers, data=payload, files=files)
        response.raise_for_status()
        return

    response = requests.post(url, headers=headers, data=payload)
    response.raise_for_status()
    return


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


# get symbol kline
# Type of candlestick patterns: 1min, 3min, 5min, 15min, 30min, 1hour, 2hour, 4hour, 6hour, 8hour, 12hour, 1day, 1week
timeFrame = "1hour"
symbols = ["BTC", "ETH","XRP", "LTC", "BCH", "KCS", "BNB", "SOL", "XMR", "MATIC","ADA", "AAVE", "APE", "MANA", "SAND", "AXS", "DOGE", "LINK", "GRT","ARB"]
# symbols = ["BTC", "ETH","XRP","LTC", "BCH", "KCS", "BNB",]

if __name__ == '__main__':
    for symbol in symbols:
        try:
            klines = client.get_kline(f'{symbol}-USDT', timeFrame)
            if klines:
                df = pd.DataFrame(klines, columns=[
                                  'Date', 'Open', 'Close', 'High', 'Low', 'Volume', 'Turn Over'])
                df['Date'] = df['Date'].astype(float)
                df['Open'] = df['Open'].astype(float)
                df['Close'] = df['Close'].astype(float)
                df['High'] = df['High'].astype(float)
                df['Low'] = df['Low'].astype(float)
                df['Volume'] = df['Volume'].astype(float)
                df['Turn Over'] = df['Turn Over'].astype(float)

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

                # Check if MACD crossover occurred in the latest row
                crossover_direction = "-"
                if df['macd_crossover'].iloc[-1]:
                    macd_value = df['macd'].iloc[-1]
                    signal_value = df['macd_signal'].iloc[-1]

                    print(
                        f"macd_crossover_up: {df['macd_crossover_up'].iloc[-1]} macd_crossover_down: {df['macd_crossover_down'].iloc[-1]}")
                    # if macd_value > signal_value:
                    #     crossover_direction = 'Bullish (Upward)'
                    # else:
                    #     crossover_direction = 'Bearish (Downward)'

                    if df['macd_crossover_up'].iloc[-1]:
                        crossover_direction = 'Bullish (Upward)'

                    elif df['macd_crossover_down'].iloc[-1]:
                        crossover_direction = 'Bearish (Downward)'
                    else:
                        crossover_direction = '-'

                # Check RSI levels
                current_rsi = df['rsi'].iloc[-1]
                is_overbought = df['overbought'].iloc[-1]
                is_oversold = df['oversold'].iloc[-1]

                if is_overbought:
                    rsi_level = 'Overbought'
                elif is_oversold:
                    rsi_level = 'Oversold'
                else:
                    rsi_level = 'Neutral'

                if df['macd_trend'].iloc[-1]:
                    current_trend_direction = 'Upward'
                else:
                    current_trend_direction = 'Downward'

                msg = f'เหรียญ {symbol}\nกำลังอยู่ในช่วง: {crossover_direction}\nเทรน: {current_trend_direction}\nRSI Level: {rsi_level}\nRSI ปัจจุบัน: {current_rsi:.2f}\nTimeframe: {timeFrame}'
                print(msg)
                if crossover_direction != "-":
                    send_line_notification(msg, None)
                    # Check folder exits!
                    if os.path.exists(f"export/{symbol}"):shutil.rmtree(f"export/{symbol}")
                    os.makedirs(f"export/{symbol}")
                    df.to_csv(f"export/{symbol}/{symbol}.csv")

                    # Plot RSI values and highlight overbought and oversold regions
                    plt.figure(figsize=(12, 6))
                    plt.plot(df['rsi'], label='RSI')
                    plt.fill_between(df.index, 70, where=df['overbought'], color='red', alpha=0.3, label='Overbought')
                    plt.fill_between(df.index, 0, where=df['oversold'], color='green', alpha=0.3, label='Oversold')
                    plt.axhline(70, color='red', linestyle='--', linewidth=1)
                    plt.axhline(30, color='green', linestyle='--', linewidth=1)
                    plt.title(f'{symbol} RSI with Overbought and Oversold Regions')
                    plt.xlabel('Date')
                    plt.ylabel('RSI')
                    plt.legend()
                    plt.grid(True)
                    # Save the chart as an image
                    rsiPath = f"export/{symbol}/{symbol}_RSI.png"
                    plt.savefig(rsiPath)
                    # plt.show()
                    send_line_notification(f"{symbol} RSI", rsiPath)

                    # Plot MACD values with crossover arrows and last price
                    plt.figure(figsize=(12, 6))
                    plt.plot(df['macd'], label='MACD')
                    plt.plot(df['macd_signal'], label='Signal')
                    plt.scatter(df.index[df['macd_crossover_up']], df['macd'][df['macd_crossover_up']], marker='^', color='green', label='Crossover Up')
                    plt.scatter(df.index[df['macd_crossover_down']], df['macd'][df['macd_crossover_down']], marker='v', color='red', label='Crossover Down')
                    # Add last price behind the arrows
                    last_prices_up = df['Close'][df['macd_crossover_up']]
                    last_prices_down = df['Close'][df['macd_crossover_down']]
                    for i, price in last_prices_up.items():
                        plt.annotate(f'{price:.2f}', (i, df['macd'][i]), textcoords="offset points", xytext=(0,10), ha='center', color='green')
                    for i, price in last_prices_down.items():
                        plt.annotate(f'{price:.2f}', (i, df['macd'][i]), textcoords="offset points", xytext=(0,-15), ha='center', color='red')

                    # Add price on the last point of the MACD line
                    last_price = df['Close'].iloc[-1]
                    plt.annotate(f'{last_price:.2f}', (df.index[-1], df['macd'].iloc[-1]), textcoords="offset points", xytext=(0,10), ha='center', color='black')
                    plt.title(f'{symbol} MACD with Crossovers and Last Price')
                    plt.xlabel('Date')
                    plt.ylabel('MACD')
                    plt.legend()
                    plt.grid(True)
                    # Save the chart as an image
                    macdPath = f"export/{symbol}/{symbol}_MACD.png"
                    plt.savefig(macdPath)
                    # plt.show()
                    send_line_notification(f"{symbol} MACD", macdPath)

                    # # Sort the DataFrame by the date column
                    df = df.iloc[::-1]
                    # Calculate MACD values
                    ema_12 = df['Close'].ewm(span=12, adjust=False).mean()
                    ema_26 = df['Close'].ewm(span=26, adjust=False).mean()

                    # Plot the candlestick chart with EMA lines
                    fig, ax = mpf.plot(df, type='candle', style='binance', addplot=[mpf.make_addplot(ema_12, color='blue'),mpf.make_addplot(ema_26, color='red')], returnfig=True)
                    plt.title(f'{symbol} Candlestick')
                    candlePath = f"export/{symbol}/{symbol}_CANDLESTICK.png"
                    plt.savefig(candlePath)
                    send_line_notification(f"{symbol} CANDLESTICK", candlePath)

        except Exception as e:
            print(e)
