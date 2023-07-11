from datetime import datetime, timedelta
import os
import shutil
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import mplfinance as mpf
import pytz
import requests
import talib

EXPORT_DIR = "export"


# SYMBOLS = ['1INCH', 'AAVE', 'ADA', 'ALGO', 'ALPHA', 'APE', 'ARB', 'ATOM', 'AVAX', 'AXS', 'BAL', 'BAND', 'BAT',
# 'BCH', 'BLUR', 'BNB', 'BTC', 'CELO', 'CHZ', 'COMP', 'CRV', 'DOGE', 'DOT', 'DYDX', 'ENJ', 'ENS', 'ETH', 'FLOW',
# 'FTM', 'FXS', 'GAL', 'GLM', 'GRT', 'HBAR', 'HFT', 'ID', 'ILV', 'IMX', 'IOST', 'KNC', 'KSM', 'LDO', 'LINK', 'LQTY',
# 'LRC', 'LUNA', 'LYXE', 'MANA', 'MATIC', 'MKR', 'NEAR', 'OCEAN', 'OMG', 'OP', 'PERP', 'SAND', 'SCRT', 'SNX', 'SOL',
# 'STG', 'SUSHI', 'TRX', 'UNI', 'XLM', 'XRP', 'XTZ', 'YFI', 'ZIL']
def get_symbols():
    symbols = []
    res = requests.request("GET", "https://api.bitkub.com/api/market/ticker")
    data = res.json()
    for symbol in data:
        symbols.append(str(symbol.replace("THB_", "")).strip())

    return symbols


def send_line_notification(line_token, message, image_path):
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


def check_rsi_overbought_oversold(df, rsi_period=14, overbought_thresh=70, oversold_thresh=30):
    df['rsi'] = talib.RSI(df['Close'], timeperiod=rsi_period)
    df['overbought'] = df['rsi'] > overbought_thresh
    df['oversold'] = df['rsi'] < oversold_thresh
    return df


def plot_chart(df, tf="1 วัน", SYMBOL=None, exportPath=""):
    ## Check RSI cross
    df = check_rsi_overbought_oversold(df)
    # Calculate EMA9 and EMA21
    df['EMA9'] = df['Close'].ewm(span=9, adjust=False).mean()
    df['EMA21'] = df['Close'].ewm(span=21, adjust=False).mean()
    # Find crossover points
    df['EMA9_above_EMA21'] = df['EMA9'] > df['EMA21']
    df['EMA9_below_EMA21'] = df['EMA9'] < df['EMA21']
    df["Diff"] = df['EMA9'].astype(float) - df['EMA21'].astype(float)
    df['Crossover'] = df['EMA9_above_EMA21'].astype(int) - df['EMA9_below_EMA21'].astype(int)

    # Determine trend (Bullish, Bearish, or Neutral)
    df['Trend'] = np.where(df['EMA9'] > df['EMA21'], 'Bullish(ขาขึ้น)',
                           np.where(df['EMA9'] < df['EMA21'], 'Bearish(ขาลง)', 'Neutral(ไม่มีการเคลื่อนไหว)'))

    # Plot the candlestick chart with EMA lines and arrows
    apds = [
        mpf.make_addplot(df['EMA9'], color='blue'),
        mpf.make_addplot(df['EMA21'], color='red'),
    ]
    mpf.plot(df, type='candle', style='binance', title=f'{SYMBOL} Kline Chart',
             ylabel='Price', ylabel_lower='Shares', addplot=apds, returnfig=True)
    obj = df.tail(1)
    # print(obj["Diff"].values)
    emaDiff = float(f"{obj['Diff'].values[0]:.2f}")
    rsiValue = float(f"{obj['rsi'].values[0]:.2f}")

    isInterest = False
    txtInterest = "ไม่แนะนำให้ลงทุน"
    if obj["EMA9_below_EMA21"].values:
        if rsiValue > 69:
            isInterest = True
            txtInterest = "ช่วงน่าสนใจ"
    if obj["EMA9_above_EMA21"].values:
        if rsiValue < 31:
            isInterest = True
            txtInterest = "ช่วงน่าสนใจ"

    msg = f"{SYMBOL} Timeframe: {tf}\nเทรนขณะนี้: {obj['Trend'].values[0]}\nอัตราEMA:{emaDiff}\nRSI Level: {rsiValue}\n{txtInterest}"
    print(
        f"{SYMBOL} Timeframe: {tf} เทรนขณะนี้: {obj['Trend'].values[0]} อัตราEMA:{emaDiff} RSI Level: {rsiValue} {txtInterest}")
    try:
        shutil.rmtree(exportPath)
    except:
        pass
    try:
        os.makedirs(exportPath)
    except:
        pass

    df.to_csv(f"{exportPath}/{SYMBOL}.csv")
    plt.savefig(f"{exportPath}/{SYMBOL}.png", format("png"))
    plt.close()

    if isInterest:
        return [msg, f"{exportPath}/{SYMBOL}.png"]

    return None


try:
    shutil.rmtree(EXPORT_DIR)
except:
    pass

try:
    os.makedirs(EXPORT_DIR)
except:
    pass


def kucoin_kline():
    # Type of candlestick patterns: 1min, 3min, 5min, 15min, 30min, 1hour, 2hour, 4hour, 6hour, 8hour, 12hour, 1day, 1week
    TIMEFRAME = "30min"
    dte = datetime.now()
    startDte = int(datetime.timestamp(dte - timedelta(hours=50)))
    endDte = int(datetime.timestamp(dte))
    for SYMBOL in get_symbols():
        if (SYMBOL not in ["USDT", "USDC", "BUSD", "TUSD", "DAI"]):
            url = f"https://openapi-v2.kucoin.com/api/v1/market/candles?type={TIMEFRAME}&symbol={SYMBOL}-USDT&startAt={startDte}&endAt={endDte}"
            res = requests.request("GET", url)
            klines = res.json()
            if klines['code'] == '200000' and len(klines['data']) > 0:
                df = pd.DataFrame(klines["data"],
                                  columns=['Date', 'Open', 'Close', 'High', 'Low', 'Volume', 'Turn Over'])
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
                df['Date'] = df['Date'].dt.tz_localize(pytz.utc).dt.tz_convert(timezone)
                df.set_index('Date', inplace=True)

                # Sort the DataFrame by the date column
                df = df.iloc[::-1]
                msg = plot_chart(df, "1 วัน", SYMBOL, f"{EXPORT_DIR}/kucoin/{SYMBOL}")
                if msg:
                    print(msg)
                    send_line_notification('BfTqtBO0kuo5mqneTdBoe5ktUAnxYrHIoaWhLRcBTwj', msg[0], msg[1])


def bitkub_kline():
    # resolution	string	Chart resolution (1, 5, 15, 60, 240, 1D)
    TIMEFRAME = "60"
    dte = datetime.now()
    startDte = int(datetime.timestamp(dte - timedelta(days=5)))
    endDte = int(datetime.timestamp(dte))

    symbols = get_symbols()
    symbols.sort()
    for SYMBOL in symbols:
        try:
            url = f"https://api.bitkub.com/tradingview/history?symbol={SYMBOL}_THB&resolution={TIMEFRAME}&from={startDte}&to={endDte}"
            res = requests.request("GET", url)
            obj = res.json()

            klines = []
            x = len(obj["c"])
            for i in range(x):
                klines.append([obj['t'][i], obj['o'][i], obj['c'][i], obj['h'][i], obj['l'][i], obj['v'][i]])

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

                df.set_index('Date', inplace=True)
                msg = plot_chart(df, "1 วัน", SYMBOL, f"{EXPORT_DIR}/bitkub/{SYMBOL}")
                if msg:
                    print(msg)
                    send_line_notification('jeCy5PHmuP5cBDQz74LvCxV0pkiGEBrtYgXvS9RBIhT', msg[0], msg[1])

        except Exception as ex:
            print(ex)
            pass


def binance_kline():
    # resolution	,1s,1m,3m,5m,15m,30m,1h,2h,4h,6h,8h,12h,1d,3d,1w,1M
    TIMEFRAME = "1h"
    symbols = get_symbols()
    symbols.sort()
    for SYMBOL in symbols:
        if (SYMBOL not in ["USDT", "USDC", "BUSD", "TUSD", "DAI"]):
            url = f"https://api.binance.com/api/v3/klines?symbol={SYMBOL}USDT&interval={TIMEFRAME}&limit=50"
            res = requests.request("GET", url)
            klines = res.json()
            if ("code" not in klines):
                df = pd.DataFrame(klines,
                                  columns=['Date', 'Open', 'High', 'Low', 'Close', 'Volume', "CloseTime", "Quote",
                                           "Number", "TakerBase", "TakerQuote", "Unused"])
                df['Date'] = df["Date"].astype(float)
                df['Open'] = df["Open"].astype(float)
                df['High'] = df["High"].astype(float)
                df['Low'] = df["Low"].astype(float)
                df['Close'] = df["Close"].astype(float)
                df['Volume'] = df["Volume"].astype(float)
                df["CloseTime"] = df["CloseTime"].astype(float)
                df["Quote"] = df["Quote"].astype(float)
                df["Number"] = df["Number"].astype(float)
                df["TakerBase"] = df["TakerBase"].astype(float)
                df["TakerQuote"] = df["TakerQuote"].astype(float)
                df["Unused"] = df["Unused"].astype(float)

                # Convert the 'Date' column to datetime format
                try:
                    df['Date'] = pd.to_datetime(df['Date'] * 1000, unit='ms')
                except ValueError:
                    df['Date'] = pd.to_datetime(df['Date'] * 1000)
                # Set the timezone for the 'Date' column
                timezone = 'Asia/Bangkok'
                df['Date'] = df['Date'].dt.tz_localize(
                    pytz.utc).dt.tz_convert(timezone)

                df.set_index('Date', inplace=True)
                msg = plot_chart(df, "1 วัน", SYMBOL, f"{EXPORT_DIR}/binance/{SYMBOL}")
                if msg:
                    print(msg)
                    send_line_notification('0gbOSCnyQVJ2y0Oc8EFmqfx2ZMVd6FUJmmuoC2Jugjg', msg[0], msg[1])


if __name__ == '__main__':
    bitkub_kline()
    kucoin_kline()
    binance_kline()
