import websocket, json, pprint, talib
import personal_function as pf
from binance.client import Client
from binance.enums import *
from datetime import datetime, timezone, timedelta
import telegram_send
import numpy as np

def on_open(ws):
    print('opened connection')

def on_close(ws):
    print('closed connection')

def on_message(ws, message):
    global time_zone,symbol
    global closes, in_position, type, quantity 
    
    #print('received message')
    json_message = json.loads(message)
    candle = json_message['k']
    time= json_message['E']
    is_candle_closed = candle['x']
    open_price= candle['o']
    high_price=candle['h']
    low_price=candle['l']
    close_price = candle['c']
    time=int(time/1000)
    time=(datetime.fromtimestamp(time,time_zone).strftime('%Y-%m-%d %H:%M:%S'))
    if is_candle_closed:
        print("{} candle closed at {}".format(time,close_price))
        closes.append(float(close_price))
        with open("bot_results.csv", "a") as f:
            f.write("{},{:.2f},{:.2f},{:.2f},{:.2f}".format(time,open_price,high_price,low_price,close_price))
        if len(closes) >= (RSI_PERIOD+1):
            np_closes = np.array(closes)
            rsi = talib.RSI(np_closes, RSI_PERIOD)
            last_rsi = rsi[-1]
            print("the current rsi is {}".format(last_rsi))
            with open("bot_results.csv", "a") as f:
                f.write(",{:.2f}".format(last_rsi)) 
            if last_rsi > RSI_OVERBOUGHT:
                if in_position:
                    print("Overbought! Sell! Sell! Sell!")
                    # put binance sell logic here
                    order = client.create_order(symbol=symbol, side=SIDE_SELL, type=type, quantity=quantity)
                    in_position = False
                    #send a message to telegram
                    time_tran=order['transactTime']
                    time_tran=int(time_tran/1000)
                    time_tran=(datetime.fromtimestamp(time_tran,time_zone).strftime('%Y-%m-%d %H:%M:%S'))
                    side=order['side']
                    qty=float(order['fills'][0]['qty'])
                    symbol=order['symbol']
                    price=float(order['fills'][0]['price'])
                    telegram_send.send(messages=['RSI_bot {} {} {:.2f} {} at {:.2f} USDT'.format(time_tran,side,qty,symbol,price)])
                    
                    print('{} {} {:.2f} {} at {:.2f} USDT'.format(time_tran,side,qty,symbol,price))
                    with open("bot_results.csv", "a") as f:
                        f.write(",SELL")
                else:
                    print("It is overbought, but we don't own any. Nothing to do.")
            
            if last_rsi < RSI_OVERSOLD:
                if in_position:
                    print("It is oversold, but you already own it, nothing to do.")
                else:
                    print("Oversold! Buy! Buy! Buy!")
                    # put binance buy order logic here
                    order = client.create_order(symbol=symbol, side=SIDE_BUY, type=type, quantity=quantity)
                    in_position = True
                    #send a message to telegram
                    time_tran=order['transactTime']
                    time_tran=int(time_tran/1000)
                    time_tran=(datetime.fromtimestamp(time_tran,time_zone).strftime('%Y-%m-%d %H:%M:%S'))
                    side=order['side']
                    qty=float(order['fills'][0]['qty'])
                    symbol=order['symbol']
                    price=float(order['fills'][0]['price'])
                    telegram_send.send(messages=['RSI_bot {} {} {:.2f} {} at {:.2f} USDT'.format(time_tran,side,qty,symbol,price)])
                    
                    print('{} {} {:.2f} {} at {:.2f} USDT'.format(time_tran,side,qty,symbol,price))
                    with open("bot_results.csv", "a") as f:
                        f.write(",BUY")
        with open("bot_results.csv", "a") as f:
            f.write('\n') 




#input
SOCKET = "wss://stream.binance.com:9443/ws/solusdt@kline_1m"
type=ORDER_TYPE_MARKET
quantity=1
RSI_PERIOD = 16
RSI_OVERBOUGHT = 65
RSI_OVERSOLD = 35 
symbol = 'SOLUSDT'
time_zone = timezone(timedelta(hours=8))
closes = []
in_position = False
client=pf.client()

telegram_send.send(messages=['Hello, RSI strategy is running'])
open("bot_results.csv", "w").close()
with open("bot_results.csv", "a") as f:
    f.write("Time,Open,High,Low,Close,RSI,Buy/Sell\n")     

ws = websocket.WebSocketApp(SOCKET, on_open=on_open, on_close=on_close, on_message=on_message)
ws.run_forever()
