import pandas as pd
import talib
import matplotlib.pyplot as plt
import numpy as np

def check_macd_crossover(df):
    df['macd'], df['macd_signal'], _ = talib.MACD(df['Close'])
    df['macd_crossover'] = ((df['macd'] > df['macd_signal']) & (df['macd'].shift() <= df['macd_signal'].shift()))
    return df

def check_rsi_overbought_oversold(df, rsi_period=14, overbought_thresh=70, oversold_thresh=30):
    df['rsi'] = talib.RSI(df['Close'], timeperiod=rsi_period)
    df['overbought'] = df['rsi'] > overbought_thresh
    df['oversold'] = df['rsi'] < oversold_thresh
    return df

# Sample usage
if __name__ == "__main__":
    # Replace 'your_data.csv' with your dataset file path or use other data retrieval methods.
    df = pd.read_csv('IXIC.csv')
    df = check_macd_crossover(df)
    df = check_rsi_overbought_oversold(df)

    df = check_macd_crossover(df)
    df = check_rsi_overbought_oversold(df)

    # Fill missing values with a specific value (e.g., -1)
    df.fillna(-1, inplace=True)

    # Plotting the MACD
    plt.figure(figsize=(10, 6))
    plt.plot(df['macd'], label='MACD')
    plt.plot(df['macd_signal'], label='Signal Line')
    plt.title('MACD')

    # Add arrows for MACD crossover
    macd_crossover = np.where(df['macd_crossover'])[0]
    plt.scatter(macd_crossover, df['macd'].iloc[macd_crossover], color='g', marker='^', label='Crossover')
    plt.scatter(macd_crossover + 1, df['macd'].iloc[macd_crossover + 1], color='r', marker='v', label='Crossover')

    plt.legend()
    plt.show()

    # Plotting the RSI
    plt.figure(figsize=(10, 6))
    plt.plot(df['rsi'], label='RSI')
    plt.axhline(y=70, color='r', linestyle='--', label='Overbought')
    plt.axhline(y=30, color='g', linestyle='--', label='Oversold')
    plt.title('RSI')

    # Add arrows for overbought and oversold conditions
    overbought = np.where(df['overbought'])[0]
    oversold = np.where(df['oversold'])[0]
    plt.scatter(overbought, df['rsi'].iloc[overbought], color='r', marker='^', label='Overbought')
    plt.scatter(oversold, df['rsi'].iloc[oversold], color='g', marker='v', label='Oversold')

    plt.legend()
    plt.show()