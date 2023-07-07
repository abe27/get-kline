from datetime import datetime
import os
import shutil
from kucoin.client import Market
import matplotlib.pyplot as plt
import mplfinance as mpf
import pandas as pd
import pytz
import talib
import requests
import logging
from supabase import create_client, Client

# eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InFraWp2dnVvc3pkZmVqemZyd2VrIiwicm9sZSI6ImFub24iLCJpYXQiOjE2ODg3MDI4MzAsImV4cCI6MjAwNDI3ODgzMH0.YqQsx_heKmqTwOlN-Ta1-XB6lTasW-5-fmZq3J9Yjwc
# tiggerDB
# OtW8CRhFEMVL3B26

url: str = "https://qkijvvuoszdfejzfrwek.supabase.co"
key: str = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InFraWp2dnVvc3pkZmVqemZyd2VrIiwicm9sZSI6ImFub24iLCJpYXQiOjE2ODg3MDI4MzAsImV4cCI6MjAwNDI3ODgzMH0.YqQsx_heKmqTwOlN-Ta1-XB6lTasW-5-fmZq3J9Yjwc"
supabase: Client = create_client(url, key)

EXPORT_DIR="kucoin/export"
try:
    shutil.rmtree(EXPORT_DIR)
except:
    pass

try:
    os.makedirs(EXPORT_DIR)
except:
    pass

client = Market(url='https://openapi-v2.kucoin.com')
LOG_FILENAME = datetime.now().strftime('kucoin_logfile_%H_%M_%S_%d_%m_%Y.log')
logging.basicConfig(filename=f"{EXPORT_DIR}/{LOG_FILENAME}",level=logging.DEBUG)   

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


# get symbol kline
# Type of candlestick patterns: 1min, 3min, 5min, 15min, 30min, 1hour, 2hour, 4hour, 6hour, 8hour, 12hour, 1day, 1week
timeFrame = "1hour"
def get_martket():
    return ['1INCH', 'AAVE', 'ADA', 'ALGO', 'ALPHA', 'APE', 'ARB', 'ATOM', 'AVAX', 'AXS', 'BAL', 'BAND', 'BAT', 'BCH', 'BLUR', 'BNB', 'BTC', 'CELO', 'CHZ', 'COMP', 'CRV', 'DOGE', 'DOT', 'DYDX', 'ENJ', 'ENS', 'ETH', 'FLOW', 'FTM', 'FXS', 'GAL', 'GLM', 'GRT', 'HBAR', 'HFT', 'ID', 'ILV', 'IMX', 'IOST', 'KNC', 'KSM', 'LDO', 'LINK', 'LQTY', 'LRC', 'LUNA', 'LYXE', 'MANA', 'MATIC', 'MKR', 'NEAR', 'OCEAN', 'OMG', 'OP', 'PERP', 'SAND', 'SCRT', 'SNX', 'SOL', 'STG', 'SUSHI', 'TRX', 'UNI', 'XLM', 'XRP', 'XTZ', 'YFI', 'ZIL']

if __name__ == '__main__':
    logging.info(f'Forecasting Job Started...')
    symbols = get_martket()
    symbols.sort()
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
                
                if is_oversold:
                    # # Sort the DataFrame by the date column
                    df = df.iloc[::-1]
                    # Calculate MACD values
                    lastPrice = df['Close'].iloc[-1]
                    sbDB = supabase.table("assets").select("id").eq("exchange","kucoin").eq("symbol",symbol).execute()
                    # Assert we pulled real data.
                    if len(sbDB.data) > 0:
                        sbDB = supabase.table("assets").update({"last_price": lastPrice, "updated_at": "now()"}).eq("exchange","kucoin").eq("symbol",symbol).execute()
                    else:
                        sbDB = supabase.table("assets").insert({
                            "exchange":"kucoin",
                            "symbol": symbol,
                            "price": lastPrice,
                            "last_price": lastPrice,
                            "status": True
                            }).execute()


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
