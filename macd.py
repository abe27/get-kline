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
                       figsize=[10, 6],
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

        msg = f'{symbol}\nตำแหน่งล่าสุดที่ {txtCross} คือ: {cross_date.strftime("%Y-%m-%d %H:%M")}\nEMA: {emaShort_latest - emaLong_latest:.2f}\nRSI: {df["rsi14"].iloc[-1].astype(float):.2f}'
        msg += f"\nอัตราการเทรดชนะ: {win_rate:.2f}%\nTimeframe: {timeFrame}"
        preRSI = df["rsi14"].iloc[-2]
        lastRSI = df["rsi14"].iloc[-1]
        df.to_csv(f"{EXPORT_DATA_DIR}/{symbol}.csv")
        plt.savefig(f"{EXPORT_DATA_DIR}/{symbol}.png", bbox_inches='tight')
        print(msg)
        if cross_date.strftime("%Y-%m-%d") == dte.strftime("%Y-%m-%d"):
            # แจ้งเตือนผ่านไลน์
            if (float(f"{emaShort_latest - emaLong_latest:.2f}") < 0.1 and float(f"{emaShort_latest - emaLong_latest:.2f}") >= -1):
                if isSpot:
                    if lastRSI <= 30 and preRSI < lastRSI:
                        send_line_notification(lineToken, msg, f"{EXPORT_DATA_DIR}/{symbol}.png")
                else:
                    send_line_notification(lineToken, msg, f"{EXPORT_DATA_DIR}/{symbol}.png")

    except Exception as e:
        print(e)
        pass


SYMBOLS = [
    "XMR",
    "CAKE",
    "ALGO",
    "XLM",
    "TRX",
    "EOS",
    "BAT",
    "OP",
    "ATOM",
    "GALA",
    "KDA",
    "NEAR",
    "IMX",
    "SIX",
    "1INCH",
    "BTC",
    "ETH",
    "XRP",
    "BNB",
    "SOL",
    "MATIC",
    "ADA",
    "APE",
    "AXS",
    "LINK",
    "LTC",
    "BCH",
    "DOGE",
    "DOT",
    "GT",
    "KUB",
    "KCS",
    "SAND",
    "MANA"]

def kucoin():
    # สร้าง Client ของ KuCoin
    api_key = '64955e9d5f668a0001837a9a'
    api_secret = '25a31dc8-f9c0-4c1c-95b5-9c23915a9f17'
    api_passphrase = 'ADSads123'
    client = kc.Client(api_key, api_secret, api_passphrase)
    # ดึงข้อมูลเกี่ยวกับราคาที่ต้องการ
    TIMEFRAME = "30min"
    SYMBOLS.sort()
    for symbol in SYMBOLS:
        dte = datetime.now()
        startDte = int(datetime.timestamp(dte - timedelta(days=3)))
        endDte = int(datetime.timestamp(dte))
        try:
            candles = client.get_kline_data(
                f"{symbol}-USDT", kline_type=TIMEFRAME, start=startDte, end=endDte)
            # สร้าง DataFrame จากข้อมูลเกี่ยวกับราคา
            df = pd.DataFrame(candles)
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

kucoin()