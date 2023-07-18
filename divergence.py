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

def send_line_notification(**kwargs):
    line_token=None
    message=None
    image_path=None

    if "line_token" in kwargs:
        line_token = kwargs["line_token"]
    
    if "message" in kwargs:
        message = kwargs["message"]
    
    if "image_path" in kwargs:
        image_path = kwargs["image_path"]

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
def get_candlestick_data(**kwargs):
    obj = kwargs
    SYMBOL="BTC"
    df = []
    EMAShort=9
    EMALong=20
    EMALongTerm=50
    EMALonger=200

    if obj["symbol"]:
        SYMBOL = obj["symbol"]
    if len(obj["data"]) > 0:
        df = obj["data"]

    if obj["emaShort"]:
        EMAShort = obj["emaShort"]

    if obj["emaLong"]:
        EMALong = obj["emaLong"]

    if obj["emaLongTerm"]:
        EMALongTerm = obj["emaLongTerm"]
    
    if obj["emaLonger"]:
        EMALonger = obj["emaLonger"]
    
    ## คำนวณเส้น EMA
    df['emaShort'] = df['close'].ewm(span=int(EMAShort)).mean()
    df['emaLong'] = df['close'].ewm(span=int(EMALong)).mean()
    df['emaLongTerm'] = df['close'].ewm(span=int(EMALongTerm)).mean()
    df['emaLongerTerm'] = df['close'].ewm(span=int(EMALonger)).mean()

    # คำนวณเส้น RSI
    df['rsi14'] = talib.RSI(df['close'], timeperiod=14)
    # ลบค่าว่าง
    df.dropna(inplace=True)
    add_plot = [
        mpf.make_addplot(df['emaShort'], color='blue', width=0.5),
        mpf.make_addplot(df['emaLong'], color='red', width=0.5),
        mpf.make_addplot(df['emaLongTerm'], color='orange', width=0.5),
        mpf.make_addplot(df['emaLongerTerm'], color='green', width=0.5),
        mpf.make_addplot(df['rsi14'], panel=2, color='red', width=0.5, ylabel='RSI'),
    ]

    fx, ax = mpf.plot(
        df, 
        type='candle', 
        style="binance", 
        title=f'{SYMBOL} Candlestick with EMA', 
        ylabel='Price',
        show_nontrading=True, 
        datetime_format='%m-%d %H:%M', 
        xrotation=20, 
        addplot=add_plot, 
        volume=True, 
        returnfig=True)
    
    image_path = f"export/kucoin/{SYMBOL}/{SYMBOL}.png"
    plt.savefig(image_path)
    df.to_csv(f"export/kucoin/{SYMBOL}/{SYMBOL}.csv")

    ### กลยุทธิ์
    isNotification = "EMA: ไม่ตัดกัน"
    crossover_points = find_ema_crossover(df,emaShort,emaLong)
    point = len(crossover_points)
    if point > 0:
        d = datetime.now()
        dte = df.index[point-1]
        # print(f"{SYMBOL} Crossover Last Points: {dte.strftime('%Y-%m-%d')}::: {d.strftime('%Y-%m-%d')}")
        if dte.strftime('%Y-%m-%d') == d.strftime('%Y-%m-%d'):
            isNotification = f"EMA: ตัดกันที่ {dte.strftime('%Y-%m-%d')}"

    msg = ""
    prevRSI = int(df["rsi14"].iloc[-2])
    lastRSI = int(df["rsi14"].iloc[-1])
    if lastRSI > 60 and prevRSI < lastRSI:
        msg = f"{SYMBOL} RSI: {prevRSI}:{lastRSI} กำลังปรับตัวขึ้น"

    if lastRSI < 40 and prevRSI > lastRSI:
        msg = f"{SYMBOL} RSI: {prevRSI}:{lastRSI} กำลังปรับตัวลง"

    else:
        if prevRSI < lastRSI:
            msg = f"{SYMBOL} RSI: {prevRSI}:{lastRSI} กำลังปรับตัวขึ้น"

        elif prevRSI > lastRSI:
            msg = f"{SYMBOL} RSI: {prevRSI}:{lastRSI} กำลังปรับตัวลง"

        else:
            msg = f"{SYMBOL} RSI: {prevRSI}:{lastRSI} กำลังลอยตัว"

    msg += f" {isNotification}"
    print(msg)
    send_line_notification(line_token="BfTqtBO0kuo5mqneTdBoe5ktUAnxYrHIoaWhLRcBTwj",message=msg,image_path=image_path)
    return df

# ตัวอย่างการใช้งาน
emaShort = 9
emaLong = 20


SYMBOLS = ["OP","NEAR","BTC","ETH","XRP","BNB","SOL","MATIC","ADA","LTC","BCH","DOT"]
def kucoin():
    # Type of candlestick patterns: 1min, 3min, 5min, 15min, 30min, 1hour, 2hour, 4hour, 6hour, 8hour, 12hour, 1day, 1week
    # ดึงข้อมูลเกี่ยวกับราคาที่ต้องการ
    TIMEFRAME = "30min"
    SYMBOLS.sort()
    for symbol in SYMBOLS:
        try:
            os.makedirs(f"export/kucoin/{symbol}")
        except:
            pass
        dte = datetime.now()
        startDte = int(datetime.timestamp(dte - timedelta(hours=28)))
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
            get_candlestick_data(symbol=symbol, data=df, emaShort=emaShort,emaLong=emaLong, emaLongTerm=50, emaLonger=200)


if __name__ == "__main__":
    kucoin()