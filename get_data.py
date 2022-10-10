import csv
from binance.client import Client
import personal_function as pf
from datetime import datetime

client = pf.Client()
csvfile = open('backtest_data.csv', 'w', newline='') 
candlestick_writer = csv.writer(csvfile, delimiter=',')

candlesticks = client.get_historical_klines("SOLUSDT", Client.KLINE_INTERVAL_1MINUTE, "1 Jan, 2022", "31 Mar, 2022")

for candlestick in  candlesticks:
    print(candlestick)
    candlestick[0] = int(candlestick[0]/1000)
    candlestick_writer.writerow(candlestick)

csvfile.close()