import matplotlib.pyplot as plt
import numpy as np
#global pnl, entry_spread, curr_spread, stock_spread, pos_multiple, pos_limit
global pos_limit, pos_multiple, stock_spread, weights
pos_limit = 40
weights = [1.0, -1.0]
pos_multiple = {"cash":0.0, "short":-1.0, "long":1.0}
stock_spread = 1.0

"""
Ideas:
    - different risk thresholds/parameters for different pairs?
    - a tick exit limit to limit holding period, or decreasing risk_threshold

TODO: 
    - covariance generator (find pairs)
    - parameter tuner / run a bunch of tests

"""



'''Returns spread, slow_mavg, fast_mavg, mavg_momentum'''
def getData(data, mavg_windows):
    slow_mavg_window = mavg_windows[0]
    fast_mavg_window = mavg_windows[1]
    momentum_window = mavg_windows[2]
    spread = []
    for line in data:
        stock1price = float(line.split(',')[0])
        stock2price = float(line.split(',')[1])
        spread.append(stock1price - stock2price)

    '''Indicators'''
    slow_mavg = []
    for i in xrange(1, slow_mavg_window):
        slow_mavg.append(movingaverage(spread[:i],i))
    slow_mavg.extend(movingaverage(spread, slow_mavg_window))

    fast_mavg = []
    for i in xrange(1, fast_mavg_window):
        fast_mavg.append(movingaverage(spread[:i],i))
    fast_mavg.extend(movingaverage(spread, fast_mavg_window))

    momentum = movingAverageDeriv(spread)
    mavg_momentum = []
    for i in xrange(1, momentum_window):
        mavg_momentum.append(movingaverage(momentum[:i],i))
    mavg_momentum.extend(movingaverage(momentum, momentum_window))

    mavgs = [slow_mavg, fast_mavg, mavg_momentum]
    return spread, mavgs

'''Indicators'''
def movingaverage (data, window):
    ret = np.cumsum(data, dtype=float)
    ret[window:] = ret[window:] - ret[:-window]
    return ret[window-1:]/window

def movingAverageDeriv(data):
    ret = [0]
    for point in xrange(len(data)-1):
        ret.append(3*(data[point+1]-data[point]))
    return ret

'''Backtest & Signal Generation'''
def adjustPosition( pnl, curr_spread, entry_spread, weights, initial, position, holdings ):
    #global pnl, entry_spread, curr_spread
    if (initial == position): return pnl, holdings
    n_pairs = pos_limit / np.sum(np.abs(weights))
    desired_holdings = list(np.multiply( n_pairs*pos_multiple[position], weights ))
    pnl -= n_pairs*stock_spread
    #print pnl
    if (position == "cash"):
        raw_trade_pnl = pos_multiple[initial]*(curr_spread-entry_spread) * n_pairs
        #print "raw trade pnl", raw_trade_pnl
        pnl += raw_trade_pnl
    
    print "Holdings: ", desired_holdings
    return pnl, desired_holdings
    
def backtest(spread, mavgs, thresholds, pnlarray):
    holdings = [0.0, 0.0]
    longs = [None]*1000
    shorts = [None]*1000
    '''Parameters'''
    stdev_window = 20
    slow_mavg = mavgs[0]
    fast_mavg = mavgs[1]
    mavg_momentum = mavgs[2]

    entry_threshold = thresholds[0]
    exit_threshold = thresholds[1]
    risk_threshold = thresholds[2]

    entry_spread = 0.0
    curr_spread = 0.0
    position = "cash"
    pnl = 0.0
    pnl_prev = 0.0
    notional = 0.0
    momentum_threshold = 0.0
    n_profitable = 0
    n_losses = 0
    for k in xrange(stdev_window, len(spread)):
        curr_spread = spread[k]
        std = np.std(spread[k-stdev_window:k])
        diff = spread[k] - slow_mavg[k]
        initial = position
        if (position == "cash"):
            if (diff >= entry_threshold*std >= 2.0*stock_spread and mavg_momentum[k] <= momentum_threshold):
                entry_spread = spread[k]
                position = "short"
                shorts[k] = entry_spread
                print "tick", k, "cash -> short", curr_spread

            elif (-diff >= entry_threshold*std >= 2.0*stock_spread and mavg_momentum[k] >= -momentum_threshold):
                entry_spread = spread[k]
                position = "long"
                longs[k] = entry_spread
                print "tick", k, "cash -> long", curr_spread
        elif (position == "short"):
            #if (diff <= exit_threshold*std and mavg_momentum[k] >= momentum_threshold):
            #if (curr_spread-entry_spread > 2.0*stock_spread and diff <= exit_threshold*std and mavg_momentum[k] >= momentum_threshold):
                #position = "cash"
                #print "short -> cash profit"
            if (diff <= exit_threshold*std and mavg_momentum[k] >= momentum_threshold):
                position = "cash"
                longs[k] = curr_spread
                print "tick", k, "short -> cash profit", curr_spread

                n_profitable += 1
            #if (mavg_momentum[k] >= momentum_threshold):
                #position = "cash"
                #print "short -> cash profit"
            elif (-diff >= risk_threshold*std):
                position = "cash"
                longs[k] = curr_spread
                print "tick", k, "short -> cash loss", curr_spread

                n_losses += 1
        elif (position == "long"):
            #if (-diff <= exit_threshold*std and mavg_momentum[k] <= -momentum_threshold):
            #if (curr_spread-entry_spread > 2.0*stock_spread and diff >= exit_threshold*std and mavg_momentum[k] <= -momentum_threshold):
                #position = "cash"
                #print "long -> cash profit"
            if (diff >= exit_threshold*std and mavg_momentum[k] <= -momentum_threshold):
                position = "cash"
                shorts[k] = curr_spread
                print "tick", k, "long -> cash profit", curr_spread

                n_profitable += 1
            #if (mavg_momentum[k] <= -momentum_threshold):
                #position = "cash"
                #print "long -> cash profit"
            elif (-diff >= risk_threshold*std):
                position = "cash" 
                shorts[k] = curr_spread
                print "tick", k, "long -> cash loss", curr_spread
                n_losses += 1

        #print k, spread[k]
        if (k == len(spread)-1):
            print "liquidating positions"
            position = "cash"
         
        pnl_prev = pnl;   
        pnl, holdings = adjustPosition( pnl, curr_spread, entry_spread, weights, initial, position, holdings )
        #print holdings
        if (initial != position and position == "cash"):
            print "pnl:", pnl

        pnlarray.append(pnl)
        #print k, position, pnl
        if (k == len(spread)-1):
            diff = pnl-pnl_prev;
            if(diff > 0):
                n_profitable += 1
            else:
                n_losses += 1
            print "pnl:", pnl, "good trades", n_profitable, "bad trades", n_losses, "total trades", n_profitable+n_losses
        
    trades = [longs, shorts]
    return pnl, trades

#@TODO
def generateBacktests():
    print "foo"

def generateThresholds():
    thresholds = []
    for i in xrange(0, 15):
        for j in xrange(0, 5):
            for k in xrange(0, 15):
                thresholds.append([i, j, k])      

#@TODO
def covariance(self, window):
    return 0

def graphStocks(data):
    stock1 = []
    stock2 = []
    stock3 = []
    for line in data:
        stock1price = float(line.split(',')[0])
        stock2price = float(line.split(',')[1])
        stock3price = float(line.split(',')[2])
        stock1.append(stock1price)
        stock2.append(stock2price)
        #stock3.append(stock3price)
    plt.plot(stock1, '-', stock2, '-', stock3, '-')
    plt.show()

    
def graph(spread, mavgs, trades, pnlarray):
    slow_mavg = mavgs[0]
    fast_mavg = mavgs[1]
    mavg_momentum = mavgs[2]
    '''Plot'''
    fig, axes = plt.subplots(nrows=3)
    #plt.plot(stock1, '-', stock2, '-', stock3, '-')
    axes[0].plot(trades[0], '^', ms = 8, color = 'g') # long
    axes[0].plot(trades[1], 'v', ms = 8, color = 'r') # short
    axes[0].plot(spread, '-')
    axes[0].plot(slow_mavg, '-')
    axes[0].plot(fast_mavg, '-')
    axes[1].plot(mavg_momentum, '-')
    axes[2].plot(pnlarray, '-')
    plt.show()

if __name__ == "__main__":
    #global pnl, entry_spread, curr_spread
    data = open("PairsRound1.csv", 'r')
    #data = open("case_data.csv", 'r')
    #graphStocks(data)


    pnlarray = []
    thresholds = [2.0, 0.0, 20.0] # entry_threshold, exit_threshold, risk_threshold
    mavg_windows = [500, 50, 20] # [slow_mavg_window, fast_mavg_window, momentum_window]
    spread, mavgs = getData(data, mavg_windows)
    pnl, trades = backtest(spread, mavgs, thresholds, pnlarray)
    #graph(spread, mavgs, trades, pnlarray)




