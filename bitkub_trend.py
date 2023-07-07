from datetime import datetime, timedelta
import os
import shutil
import matplotlib.pyplot as plt
import mplfinance as mpf
import pandas as pd
import pytz
import talib
import requests
import logging

EXPORT_DIR="export/bitkub"
try:
    # shutil.rmtree(EXPORT_DIR)
    os.makedirs(EXPORT_DIR)
except:
    pass

LOG_FILENAME = datetime.now().strftime('bitkub_logfile_%H_%M_%S_%d_%m_%Y.log')
logging.basicConfig(filename=f"export/{LOG_FILENAME}",level=logging.DEBUG)   

def send_line_notification(message, image_path):
    line_token = 'jeCy5PHmuP5cBDQz74LvCxV0pkiGEBrtYgXvS9RBIhT'
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


# resolution	string	Chart resolution (1, 5, 15, 60, 240, 1D)
timeFrame = "60"
def get_symbols():
    symbols = []
    res = requests.request("GET", "https://api.bitkub.com/api/market/ticker")
    data = res.json()
    for symbol in data:
        symbols.append(str(symbol.replace("THB_", "")).strip())
    
    return symbols
if __name__ == '__main__':
    try:
        # shutil.rmtree(EXPORT_DIR)
        os.makedirs(EXPORT_DIR)
    except:
        pass
    logging.info(f'Forecasting Job Started...')
    symbols = get_symbols()
    symbols.sort()
    for symbol in symbols:
        try:
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

            if klines:
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
                df = check_rsi(df)

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

                msg = f'เหรียญ {symbol}\nRSI Level: {rsi_level}\nRSI ปัจจุบัน: {current_rsi:.2f}\nTimeframe: {timeFrame}'
                logging.debug(f'เหรียญ {symbol} RSI Level: {rsi_level} RSI ปัจจุบัน: {current_rsi:.2f} Timeframe: {timeFrame}')
                

                # # Sort the DataFrame by the date column
                # df = df.iloc[::-1]
                # Calculate MACD values
                emaShort = df['Close'].ewm(span=5, adjust=False).mean()
                emaMedium = df['Close'].ewm(span=10, adjust=False).mean()
                emaLong = df['Close'].ewm(span=30, adjust=False).mean()
                # Plot the candlestick chart with EMA lines
                fig, ax = mpf.plot(df, type='candle', style='binance', addplot=[
                               mpf.make_addplot(emaShort, color='blue'),
                               mpf.make_addplot(emaMedium, color='red'),
                               mpf.make_addplot(emaLong, color='orange')
                            ], returnfig=True)
                
                plt.title(f'{symbol} Candlestick')
                candlePath = f"{EXPORT_DIR}/{symbol}/{symbol}_CANDLESTICK.png"

                isOnRule = False
                if is_overbought == True and current_rsi >= 65:
                    isOnRule = True

                elif is_oversold == True and current_rsi <= 45:
                    isOnRule = True

                if isOnRule:
                    try:
                        os.makedirs(f"{EXPORT_DIR}/{symbol}")
                        plt.savefig(candlePath)
                        send_line_notification(msg, candlePath)
                    except:
                        pass

        except Exception as e:
            print(e)
            logging.error(str(e))

    logging.info(f'Forecasting Job Stoped...')
