from datetime import datetime, timedelta
import os
import shutil
import kucoin.client as kc
import matplotlib.pyplot as plt
import mplfinance as mpf
import numpy as np
import pandas as pd
import pytz
import requests
import talib

try:
    shutil.rmtree("export")
except:
    pass


def send_line_notification(line_token, message, image_path):
    url = 'https://notify-api.line.me/api/notify'
    headers = {'Authorization': f'Bearer {line_token}'}
    payload = {
        "message": message
    }
    try:
        if image_path:
            files = {
                "imageFile": open(image_path, "rb")
            }
            response = requests.post(url, headers=headers,
                                    data=payload, files=files)
            response.raise_for_status()
        return
    except:
        pass

    response = requests.post(url, headers=headers, data=payload)
    response.raise_for_status()
    return


def plot_data(exchange, symbol, df, timeFrame, short=9, long=21, longTerm=50, lineToken=None, isSpot=False):
    EXPORT_DATA_DIR = f"export/{exchange}/{symbol}"
    try:
        shutil.rmtree(EXPORT_DATA_DIR)
    except:
        pass

    try:
        os.makedirs(EXPORT_DATA_DIR)
    except:
        pass

    dte = datetime.now()
    # คำนวณเส้น EMA
    df['emaShort'] = df['close'].ewm(span=int(short)).mean()
    df['emaLong'] = df['close'].ewm(span=int(long)).mean()
    df['emaLongTerm'] = df['close'].ewm(span=int(longTerm)).mean()

    # คำนวณเส้น RSI
    df['rsi14'] = talib.RSI(df['close'], timeperiod=14)
    # ลบค่าว่าง
    df.dropna(inplace=True)

    # หาค่าเส้น emaShort และ emaLong
    emaShort = df['emaShort'].values
    emaLong = df['emaLong'].values

    # หาจุดที่เส้น emaShort และ emaLong ตัดขึ้น
    cross_up_points = np.where(np.diff(np.sign(emaShort - emaLong)) > 0)[0]

    # หาจุดที่เส้น emaShort และ emaLong ตัดลง
    cross_down_points = np.where(np.diff(np.sign(emaShort - emaLong)) < 0)[0]

    add_plot = [
        mpf.make_addplot(df['emaShort'], color='blue'),
        mpf.make_addplot(df['emaLong'], color='red'),
        mpf.make_addplot(df['emaLongTerm'], color='orange'),
        mpf.make_addplot(df['rsi14'], panel=2, color='blue', ylabel='RSI'),
    ]

    fig, ax = mpf.plot(df,
                       type='candle',
                       style="binance",
                       addplot=add_plot,
                       title=f'{symbol} Candlestick Chart with EMA and RSI',
                       ylabel='Price',
                       figsize=[20, 8],
                       volume=True,
                       show_nontrading=True,
                       returnfig=True)

    # # แสดงจุดที่เส้น emaShort และ emaLong ตัดขึ้นและตัดลง
    # ax[0].scatter(df.index[cross_up_points], df['close'].values[cross_up_points], color='green', marker='^', label='Cross Up')
    # ax[0].scatter(df.index[cross_down_points], df['close'].values[cross_down_points], color='red', marker='v', label='Cross Down')
    # ax[0].legend()

    try:
        emaShort_latest = df['emaShort'].iloc[-1]
        emaLong_latest = df['emaLong'].iloc[-1]

        isCross = "-"
        txtCross = ""
        if emaShort_latest > emaLong_latest:
            txtCross = f"EMA{short} ตัดขึ้นเหนือ EMA{long}"
            isCross = "UP"

        elif emaShort_latest < emaLong_latest:
            txtCross = f"EMA{short} ตัดลงใต้ EMA{long}"
            isCross = "DOWN"

        else:
            txtCross = f"EMA{short} และ EMA{long} ไม่มีการตัดกัน"
            isCross = "-"

        df["cross_up_or_down"] = isCross
        cross_points = np.where(
            np.diff(np.sign(df['emaShort'] - df['emaLong'])) != 0)[0]
        latest_cross_point = cross_points[-1]

        cross_date = df.index[latest_cross_point]

        # หาจำนวนการตัดกันชนะและการตัดกันเสีย
        cross_up_count = len(cross_up_points)
        cross_down_count = len(cross_down_points)

        # หาจำนวนการตัดกันทั้งหมด
        total_cross_count = cross_up_count + cross_down_count

        # คำนวณเปอร์เซ็นต์การตัดกันชนะ
        win_rate = (cross_up_count / total_cross_count) * 100

        msg = f'{symbol}\nตำแหน่งล่าสุดที่ {txtCross} คือ: {cross_date.strftime("%Y-%m-%d %H:%M")}\nEMA: {emaShort_latest - emaLong_latest:.2f}\nRSI: {df["rsi14"].iloc[-13].astype(float):.2f}/{df["rsi14"].iloc[-1].astype(float):.2f}'
        
        preRSI = df["rsi14"].iloc[-2]
        lastRSI = df["rsi14"].iloc[-1]
        txtTrend = ""
        if (lastRSI < 40 and preRSI > lastRSI):
            txtTrend = "\nกำลังปรับตัวลง"

        elif (lastRSI > 60 and preRSI < lastRSI):
            txtTrend = "\nกำลังปรับตัวขึ้น"
        
        else:
            txtTrend = "\กำลังลอยตัว"

        msg += txtTrend
        msg += f"\nอัตราการเทรดชนะ: {win_rate:.2f}%\nTimeframe: {timeFrame}"
        
        df.to_csv(f"{EXPORT_DATA_DIR}/{symbol}.csv")
        plt.savefig(f"{EXPORT_DATA_DIR}/{symbol}.png", bbox_inches='tight')
        print(msg)
        if cross_date.strftime("%Y-%m-%d") == dte.strftime("%Y-%m-%d"):
            # แจ้งเตือนผ่านไลน์
            if (float(f"{emaShort_latest - emaLong_latest:.2f}") < 0.1 and float(f"{emaShort_latest - emaLong_latest:.2f}") >= -1):
                if isSpot:
                    if lastRSI < 35 and preRSI < lastRSI:
                        send_line_notification(lineToken, msg, f"{EXPORT_DATA_DIR}/{symbol}.png")
                else:
                    send_line_notification(lineToken, msg, f"{EXPORT_DATA_DIR}/{symbol}.png")

    except Exception as e:
        print(e)
        pass


SYMBOLS = ["OP","NEAR","BTC","ETH","XRP","BNB","SOL","MATIC","ADA","APE","LINK","LTC","BCH","DOGE","DOT","KUB","KCS","SAND", "XLM"]

def kucoin():
    # ดึงข้อมูลเกี่ยวกับราคาที่ต้องการ
    TIMEFRAME = "1hour"
    SYMBOLS.sort()
    for symbol in SYMBOLS:
        dte = datetime.now()
        startDte = int(datetime.timestamp(dte - timedelta(days=3)))
        endDte = int(datetime.timestamp(dte))
        try:
            url = f"https://openapi-v2.kucoin.com/api/v1/market/candles?type={TIMEFRAME}&symbol={symbol}-USDT&startAt={startDte}&endAt={endDte}"
            res = requests.request("GET", url)
            klines = res.json()
            if klines['code'] == '200000' and len(klines['data']) > 0:
                df = pd.DataFrame(klines["data"])
                # สร้าง DataFrame จากข้อมูลเกี่ยวกับราคา
                df.columns = ['time', 'open', 'close', 'high', 'low', 'volume', 'turnover']
                df['time'] = pd.to_datetime((df['time']).astype(float) * 1000, unit='ms')
                timezone = 'Asia/Bangkok'
                df['time'] = df['time'].dt.tz_localize(pytz.utc).dt.tz_convert(timezone)

                # แปลงคอลัมน์เป็นชนิดข้อมูลที่ถูกต้อง
                df[['open', 'close', 'high', 'low', 'volume', 'turnover']] = df[[
                    'open', 'close', 'high', 'low', 'volume', 'turnover']].astype(float)
                df = df.iloc[::-1]
                # กำหนดการพล็อตกราฟแท่งเทียนและเส้น EMA และเส้น RSI
                df.set_index('time', inplace=True)
                plot_data("KUCOIN", symbol, df, TIMEFRAME,9,21,50, 'BfTqtBO0kuo5mqneTdBoe5ktUAnxYrHIoaWhLRcBTwj')
        except:
            pass

def bitkub_kline():
    # resolution	string	Chart resolution (1, 5, 15, 60, 240, 1D)
    # ดึงข้อมูลเกี่ยวกับราคาที่ต้องการ
    TIMEFRAME = "60"
    SYMBOLS.sort()
    for symbol in SYMBOLS:
        dte = datetime.now()
        startDte = int(datetime.timestamp(dte - timedelta(days=5)))
        endDte = int(datetime.timestamp(dte))
        try:
            for symbol in SYMBOLS:
                try:
                    url = f"https://api.bitkub.com/tradingview/history?symbol={symbol}_THB&resolution={TIMEFRAME}&from={startDte}&to={endDte}"
                    res = requests.request("GET", url)
                    obj = res.json()

                    klines = []
                    x = len(obj["c"])
                    for i in range(x):
                        klines.append([obj['t'][i], obj['o'][i], obj['c'][i], obj['h'][i], obj['l'][i], obj['v'][i]])

                    if klines:
                        df = pd.DataFrame(klines)
                        df.columns = ['time', 'open', 'close', 'high', 'low', 'volume']
                        # แปลงคอลัมน์เป็นชนิดข้อมูลที่ถูกต้อง
                        df[['open', 'close', 'high', 'low', 'volume']] = df[['open', 'close', 'high', 'low', 'volume']].astype(float)

                        # Convert the 'Date' column to datetime format
                        try:
                            df['time'] = pd.to_datetime(df['time'] * 1000, unit='ms')
                        except ValueError:
                            df['time'] = pd.to_datetime(df['time'] * 1000, unit='s')

                        # Set the timezone for the 'Date' column
                        timezone = 'Asia/Bangkok'
                        df['time'] = df['time'].dt.tz_localize(
                            pytz.utc).dt.tz_convert(timezone)

                        # กำหนดการพล็อตกราฟแท่งเทียนและเส้น EMA และเส้น RSI
                        df.set_index('time', inplace=True)
                        plot_data("BITKUB", symbol, df, "1hour",9,21,50, 'jeCy5PHmuP5cBDQz74LvCxV0pkiGEBrtYgXvS9RBIhT', True)

                except:
                    pass
        except:
            pass

if __name__ == '__main__':
    # bitkub_kline()
    kucoin()
