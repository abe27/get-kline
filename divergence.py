from datetime import datetime, timedelta
import os
import shutil
import pandas as pd
import numpy as np
import mplfinance as mpf
import matplotlib.pyplot as plt
import pytz
import requests
import talib

try:
    shutil.rmtree("export")
except:
    pass


# คำนวณ Exponential Moving Average (EMA)
def calculate_ema(data, period):
    ema = data['close'].ewm(span=period, adjust=False).mean()
    return ema


# หาจุดที่ EMA ตัดกัน
def find_ema_crossover(data, short, long):
    emaShort = calculate_ema(data, short)
    emaLong = calculate_ema(data, long)
    
    crossover_points = np.where((emaShort.shift(1) < emaLong.shift(1)) & (emaShort > emaLong))[0]
    return crossover_points


# ดึงข้อมูลแท่งเทียนจากไฟล์ CSV หรือแหล่งข้อมูลอื่นๆ 9,20,50,200
def get_candlestick_data(SYMBOL="BTC", df=[], short=9, long=20):
     # คำนวณเส้น EMA
    df['emaShort'] = df['close'].ewm(span=int(short)).mean()
    df['emaLong'] = df['close'].ewm(span=int(long)).mean()
    df['emaLongTerm'] = df['close'].ewm(span=50).mean()
    df['emaLongerTerm'] = df['close'].ewm(span=200).mean()

    # คำนวณเส้น RSI
    df['rsi14'] = talib.RSI(df['close'], timeperiod=14)
    # ลบค่าว่าง
    df.dropna(inplace=True)
    add_plot = [
        mpf.make_addplot(df['emaShort'], color='green', width=0.5),
        mpf.make_addplot(df['emaLong'], color='red', width=0.5),
        mpf.make_addplot(df['emaLongTerm'], color='orange', width=0.5),
        mpf.make_addplot(df['emaLongerTerm'], color='yellow', width=0.5),
        mpf.make_addplot(df['rsi14'], panel=2, color='red', width=0.5, ylabel='RSI'),
    ]

    crossover_points = find_ema_crossover(df,emaShort,emaLong)

    point = len(crossover_points)
    if point > 0:
        dte = df.index[point-1]
        print(f"{SYMBOL} Crossover Last Points: {dte.strftime('%Y-%m-%d')}")

    fx, ax = mpf.plot(
        df, 
        type='candle', 
        style="binance", 
        title=f'{SYMBOL} Candlestick with EMA', 
        ylabel='Price',
        show_nontrading=True, 
        datetime_format='%Y-%m-%d', 
        xrotation=20, 
        addplot=add_plot, 
        volume=True, 
        returnfig=True)
    plt.savefig(f"export/kucoin/{SYMBOL}/{SYMBOL}.png")

    return df

# ตัวอย่างการใช้งาน
emaShort = 15
emaLong = 30


SYMBOLS = ["BTC", "ETH", "BNB", "XRP", "ADA", "SOL", "SAND"]
def kucoin():
    # Type of candlestick patterns: 1min, 3min, 5min, 15min, 30min, 1hour, 2hour, 4hour, 6hour, 8hour, 12hour, 1day, 1week
    # ดึงข้อมูลเกี่ยวกับราคาที่ต้องการ
    TIMEFRAME = "1hour"
    SYMBOLS.sort()
    for symbol in SYMBOLS:
        try:
            os.makedirs(f"export/kucoin/{symbol}")
        except:
            pass
        dte = datetime.now()
        startDte = int(datetime.timestamp(dte - timedelta(days=5)))
        endDte = int(datetime.timestamp(dte))
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
            get_candlestick_data(symbol, df, emaShort,emaLong)

if __name__ == "__main__":
    kucoin()