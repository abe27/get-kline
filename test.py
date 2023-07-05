import pandas as pd
import matplotlib.pyplot as plt
import mplfinance as mpf
import talib

# Generate sample OHLC data
ohlc_data = pd.DataFrame({'date': pd.date_range(start='2023-01-01', periods=100),
                          'open': [100, 105, 110, 115, 120] * 20,
                          'high': [120, 125, 130, 135, 140] * 20,
                          'low': [90, 95, 100, 105, 110] * 20,
                          'close': [115, 120, 125, 130, 135] * 20})

# Convert the date column to datetime type
ohlc_data['date'] = pd.to_datetime(ohlc_data['date'])

# Set the date column as the index
ohlc_data.set_index('date', inplace=True)

# Calculate MACD values
macd, macd_signal, _ = talib.MACD(ohlc_data['close'])

# Create a DataFrame for MACD data
macd_data = pd.DataFrame({'macd': macd, 'macd_signal': macd_signal}, index=ohlc_data.index)

# Create a figure and subplots
fig, (ax1, ax2) = plt.subplots(nrows=2, ncols=1, figsize=(12, 8), sharex=True)

# Plot the candlestick chart in the first subplot
mpf.plot(ohlc_data, ax=ax1, type='candle', style='binance')

# Set axis labels and title for the first subplot
ax1.set_ylabel('Price')
ax1.set_title('Candlestick Chart')

# Plot the MACD in the second subplot
ax2.plot(macd_data.index, macd_data['macd'], label='MACD')
ax2.plot(macd_data.index, macd_data['macd_signal'], label='Signal')

# Set axis labels and title for the second subplot
ax2.set_xlabel('Date')
ax2.set_ylabel('MACD')
ax2.set_title('MACD Indicator')

# Show the legend
ax2.legend()

# Adjust the spacing between subplots
plt.tight_layout()

# Show the plot
plt.show()
