import matplotlib.pyplot as plt
import numpy as np
import csv

stock_spread = 1.0
pos_multiple = {"cash":0.0, "short":-1.0, "long":1.0}
entry_spread = 0.0
curr_spread = 0.0

def ema(self, data, window):
    if len(data) < 2 * window:
        raise ValueError("data is too short")
    c = 2.0 / (window + 1)
    current_ema = self.sma(data[-window*2:-window], window)
    for value in data[-window:]:
        current_ema = (c * value) + ((1 - c) * current_ema)
    return current_ema

def movingaverage (data, window):
    ret = np.cumsum(data, dtype=float)
    ret[window:] = ret[window:] - ret[:-window]
    return ret[window-1:]/window

def movingAverageDeriv(data):
    ret = [0]
    for point in xrange(len(data)-1):
        ret.append(10*(data[point+1]-data[point]))
    return ret

#def signalGeneration():
#    '''
#    if more than $x away from the moving average, consider entry
#    enter if moving average of momentum is zero
#    exit upon stop loss or (reversion AND moving average of momentum is zero)
#    '''
#    print foo
    
def adjust_position(  weights, initial, position, holdings, pnl, position_limit):
    if (initial == position): return (holdings, 0.0)
    n_pairs = position_limit / np.sum(np.abs(weights))
    desired_holdings = list(np.multiply( n_pairs*pos_multiple[position], weights ))
    change = desired_holdings 
    for k in xrange(len(holdings)):
        change[k] -= holdings[k]
    pnl_curr = -np.sum(np.abs(change))*stock_spread/2.0
    if (position == "cash"):
        pnl_curr += (curr_spread-entry_spread) * n_pairs
    return (holdings, pnl+pnl_curr)
    
def covariance(self, window):
    return 0
    

if __name__ == "__main__":

    data = open("PairsRound1.csv", 'r')
    stock1 = []
    stock2 = []
    stock3 = []
    spread = []
    pnlarray = [0]*50
    x = [] 
    y = []
    z = []


    count = 0;
    for line in data:
    	count += 1
        '''Charting the stocks'''
        #stock1.append(line.split(',')[0])
        #stock2.append(line.split(',')[1])
        #stock3.append(line.split(',')[2])
        '''Charting the spread'''
        stock1price = float(line.split(',')[0])
        stock2price = float(line.split(',')[1])
        #stock3price = float(line.split(',')[2])
        spread.append(stock1price - stock2price)
        print(count)
        print(stock1price-stock2price)
        #ema.append()
        x.append(0)
        y.append(2)
        z.append(-2)

    
    '''Indicators'''
    window1 = 500
    window2 = 50

    slow_mavg = []
    for i in xrange(1, window1):
        slow_mavg.append(movingaverage(spread[:i],i))
    slow_mavg.extend(movingaverage(spread, window1))

    fast_mavg = []
    for i in xrange(1, window2):
        fast_mavg.append(movingaverage(spread[:i],i))
    fast_mavg.extend(movingaverage(spread, window2))

    momentum = movingAverageDeriv(spread)
    mavgmomentum = movingaverage(momentum, 20)
    
    
    '''Backtest'''
    holdings = [0.0, 0.0]
    weights = [1.0, -1.0]
    stdev_window = 50
    position_limit = 40
    entry_threshold = 5.0 #sigma
    exit_threshold = 0.0 #sigma
    risk_threshold = 10000000.0 #sigma
    position = "cash"
    pnl = 0.0
    notional = 0.0
    momentum_threshold = 0.2
    for k in xrange(stdev_window, len(spread)):
        curr_spread = spread[k]
        std = np.std(spread[k-stdev_window:k])
        diff = spread[k] - slow_mavg[k]
        initial = position
        if (position == "cash"):
            if (diff >= entry_threshold*std and mavgmomentum[k] <= momentum_threshold):
                entry_spread = spread[k]
                position = "short"
                print "cash -> short"
            elif (-diff >= entry_threshold*std and mavgmomentum[k] >= -momentum_threshold):
                entry_spread = spread[k]
                position = "long"
                print "cash -> long"
        
        elif (position == "short"):
#            if (diff <= exit_threshold*std and mavgmomentum[k] >= momentum_threshold):
            if (curr_spread-entry_spread > 2.0*stock_spread and mavgmomentum[k] >= momentum_threshold):
                position = "cash"
                print "short -> cash profit"
            elif (diff >= risk_threshold*std):
                position = "cash"
                print "short -> cash loss"
        
        elif (position == "long"):
#            if (-diff <= exit_threshold*std and mavgmomentum[k] <= -momentum_threshold):
            if (curr_spread-entry_spread > 2.0*stock_spread and mavgmomentum[k] <= -momentum_threshold):
                position = "cash"
                print "long -> cash profit"
            elif (-diff >= risk_threshold*std):
                position = "cash" 
                print "long -> cash loss"

        if (k == len(spread)-1):
            position = "cash"
        (holdings, pnl) = adjust_position( weights, initial, position, holdings, pnl, position_limit )
        

        if (initial != position and position == "cash"):
            print "pnl:", pnl

        pnlarray.append(pnl) 
        print k, position


    '''Plot Stocks'''
    fig, axes = plt.subplots(nrows=3)
    #plt.plot(stock1, '-', stock2, '-', stock3, '-')
    '''Plot spread'''
    axes[0].plot(spread, '-')
    #plt.plot(y, '-')
    #plt.plot(z, '-')
    #plt.plot(x, '-')
    '''Indicators'''
    axes[0].plot(slow_mavg, '-')
    axes[0].plot(fast_mavg, '-')
    axes[1].plot(mavgmomentum, '-')
    '''PnL'''
    axes[2].plot(pnlarray)
    plt.show()