import backtrader as bt
import datetime
import matplotlib.pyplot as plt

class RSIStrategy(bt.Strategy):
    #params = (('period', 20),)
    def log(self, txt, dt=None):
        #Print function
        dt = dt or self.datas[0].datetime.datetime(0)
        with open('backtest_results.txt', 'a') as f:
            f.write('%s, %s' % (dt.isoformat(), txt))
            f.write('\n')

    def __init__(self):
        # Initializing...
        self.dataclose = self.datas[0].close
        self.order = None
        self.buyprice = None
        self.buycomm = None
        self.rsi = bt.talib.RSI(self.data, timeperiod=RSI_period)

    def notify_order(self, order):
        if order.status in [order.Submitted, order.Accepted]:
            # Buy/Sell order submitted/accepted to/by broker - Nothing to do
            return

        # Check if an order has been completed
        # Attention: broker could reject order if not enough cash
        if order.status in [order.Completed]:
            if order.isbuy():
                self.log(
                    'BUY EXECUTED, Price: %.2f, Cost: %.2f, Comm %.2f' %
                    (order.executed.price,
                     order.executed.value,
                     order.executed.comm))

                self.buyprice = order.executed.price
                self.buycomm = order.executed.comm
            else:  # Sell
                self.log('SELL EXECUTED, Price: %.2f, Cost: %.2f, Comm %.2f' %
                         (order.executed.price,
                          order.executed.value,
                          order.executed.comm))

            self.bar_executed = len(self)

        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.log('Order Canceled/Margin/Rejected')

        # Write down: no pending order
        self.order = None

    def notify_trade(self, trade):
        global profit
        if not trade.isclosed:
            return

        self.log('OPERATION PROFIT, GROSS %.2f, NET %.2f' %
                 (trade.pnl, trade.pnlcomm))
        profit=profit+trade.pnlcomm
        # To keep track of pending orders and buy price/commission
        self.order = None
        self.buyprice = None
        self.buycomm = None
        

    def next(self):
        #self.log('Close, %.2f' % self.dataclose[0])
        if self.order:
            return
        
        if not self.position:
            if self.rsi < oversold:
                self.log('BUY CREATE, %.2f' % self.dataclose[0])
                self.order=self.buy()
        
        else:
            if self.rsi > overbought:
                self.log('SELL CREATE, %.2f' % self.dataclose[0])
                self.order=self.sell()

def saveplots(cerebro, numfigs=1, iplot=True, start=None, end=None,
             width=16, height=9, dpi=50, tight=True, use=None, file_path = '', **kwargs):

        from backtrader import plot
        if cerebro.p.oldsync:
            plotter = plot.Plot_OldSync(**kwargs)
        else:
            plotter = plot.Plot(**kwargs)

        figs = []
        for stratlist in cerebro.runstrats:
            for si, strat in enumerate(stratlist):
                rfig = plotter.plot(strat, figid=si * 10,
                                    numfigs=numfigs, iplot=iplot,
                                    start=start, end=end, use=use,width=1600, height=900,dpi=2000)
                figs.append(rfig)

        for fig in figs:
            for f in fig:
                f.savefig(file_path, bbox_inches='tight')
        return figs



#variables
#For cerebro
data_name='backtest_data.csv'
slip_perc=0.005 
set_cash=1000 
set_commission=0.001
profit=0

#For RSI
RSI_period=20
overbought=85
oversold=15

#main
open("backtest_results.txt", "w").close() #to erase all the information from the previous run

#initialize cerebro
cerebro = bt.Cerebro()
data = bt.feeds.GenericCSVData(
    dataname=data_name, 
    dtformat=2, 
    #compression=15, 
    timeframe=bt.TimeFrame.Minutes,
    )
cerebro.addstrategy(RSIStrategy)
cerebro.broker = bt.brokers.BackBroker(slip_perc=slip_perc,slip_open=True,slip_match=True, slip_out=False)
cerebro.adddata(data)
cerebro.broker.setcash(set_cash)
cerebro.broker.setcommission(commission=set_commission)
cerebro.addsizer(bt.sizers.FixedSize, stake=1)
with open('backtest_results.txt', 'a') as f:
    f.write("The commission is {}% and the slippage is {}%.\n".format(set_commission*100,slip_perc*100))
    f.write('Starting Portfolio Value: %.2f\n' % cerebro.broker.getvalue())
cerebro.run()
with open('backtest_results.txt', 'a') as f:
    f.write('Final Portfolio Value: %.2f\n' % cerebro.broker.getvalue())
    f.write('The overall profit: %.2f\n' %profit)
#note that we can see the difference between the final and the intial portfolio is not equal
#to the overall profit. It is because the final executation is a BUY. 
#so the final portfolio is cash+ the price of the stock of the last price - the last commission fee.
#cerebro.plot()
#figure = cerebro.plot()
#figure.savefig('example.png')
saveplots(cerebro, file_path = 'backtest.png') #run it