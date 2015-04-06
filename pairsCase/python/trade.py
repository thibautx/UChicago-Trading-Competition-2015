import matplotlib.pyplot as plt
import numpy as np
import numpy.linalg as npla
from statsmodels.tsa.stattools import adfuller

#global pnl, entry_spread, curr_spread, stock_spread, pos_multiple, pos_limit
global pos_limit, pos_multiple, stock_spread, weights
pos_limit = 40
weights = [1.0, -1.0]
pos_multiple = {"cash":0.0, "short":-1.0, "long":1.0}
stock_spread = 1.0

ORDER_POWER = 2
ENSURE_MIN_SPREAD_BUYBACK = False
NO_STD = False

"""
Ideas:
    - different risk thresholds/parameters for different pairs?
    - a tick exit limit to limit holding period, or decreasing risk_threshold

TODO: 
    - covariance generator (find pairs)
    - parameter tuner / run a bunch of tests

"""


def ExpMovingAverage(values, window):
    weights = np.exp(np.linspace(-1., 0., window))
    weights /= weights.sum()
    # Here, we will just allow the default since it is an EMA
    a = np.convolve(values, weights)[:len(values)]
    a[:window] = a[window]
    return a #again, as a numpy array.


'''Returns spread, slow_mavg, fast_mavg, mavg_momentum'''
def getData(data, mavg_windows, stock1=0, stock2=1, coint_vect=[1, -1], alpha=0.2):
    slow_mavg_window = mavg_windows[0]
    fast_mavg_window = mavg_windows[1]
    momentum_window = mavg_windows[2]
    spread = []
    for line in data:
        prices = map(float, line.split(','))
        stock1price = float(line.split(',')[stock1])
        stock2price = float(line.split(',')[stock2])
        spread.append(np.dot(np.array(coint_vect), np.array([stock1price, stock2price])))

    '''Indicators'''
    slow_mavg = []
    for i in xrange(1, slow_mavg_window):
        slow_mavg.append(movingaverage(spread[:i],i))
    slow_mavg.extend(movingaverage(spread, slow_mavg_window))

    fast_mavg = [spread[0]]
    for i in xrange(1, len(spread)):
        fast_mavg.append(((1-alpha)*fast_mavg[i-1] + alpha*spread[i]))
    #fast_mavg.extend(movingaverage(spread, fast_mavg_window))

    #fast_mavg = ExpMovingAverage(spread, fast_mavg_window)

    momentum = movingAverageDeriv(spread)
    momentum = np.diff(fast_mavg)
    mavg_momentum = np.concatenate([[momentum[0]], np.diff(fast_mavg)])
    #mavg_momentum = [momentum[0]]
    #for i in xrange(1, momentum_window):
    #    mavg_momentum.append(movingaverage(momentum[:i],i))
    #mavg_momentum.extend(movingaverage(momentum, momentum_window))

    mavgs = [slow_mavg, fast_mavg, mavg_momentum]

    return spread, mavgs

'''Indicators'''
def movingaverage (data, window):
    ret = np.cumsum(data, dtype=float)
    ret[window:] = ret[window:] - ret[:-window]
    return ret[window-1:]/window

def movingAverageDeriv(data):
    ret = []
    for point in xrange(len(data)-1):
        ret.append(3*(data[point+1]-data[point]))
    return ret

    
def backtest(spread, mavgs, thresholds, order_qty, pnlarray, mavg_windows, start, order_qty_base, benchmark=False):
    global stock_spread
    holdings = [0.0, 0.0]
    longs = [None]*1000
    shorts = [None]*1000
    '''Parameters'''

    slow_mavg = mavgs[0]
    fast_mavg = mavgs[1]
    mavg_momentum = mavgs[2]
    slow_mavg_window = mavg_windows[0]
    fast_mavg_window = mavg_windows[1]
    momentum_window = mavg_windows[2]
    stdev_window = mavg_windows[3]
    if not benchmark:
        pnlarray += [0]*start
    #stdev_window = slow_mavg_window


    entry_threshold = thresholds[0]
    exit_threshold = thresholds[1]
    entry_spread = 0.0
    curr_spread = 0.0
    position = 0
    d_position = 0
    cash = 0.0
    pnl = 0.0
    pnl_prev = 0.0
    notional = 0.0

    n_profitable = 0
    n_losses = 0

    if benchmark:
        positions = []
        threshold_series = []
    else:
        positions = [0]*start
        threshold_series = [0]*start

    if benchmark:
        start = 0
        entry_threshold = 5
        exit_threshold = 1
        stock_spread = 0
        order_qty = 0
        order_qty_base = 2

    for k in xrange(start, len(spread)):

        if k == 142:
            pass

        curr_spread = spread[k]
        if benchmark:
            std = 1.0
        else:
            std = np.std(spread[k-min(k, stdev_window):k])
            if NO_STD:
                std = 1.0
        diff = spread[k] - slow_mavg[k]
        initial = position

        d_position = 0

        threshold_series.append(entry_threshold*std)

        if abs(2*position) < pos_limit:
            if diff >= entry_threshold*std and diff >= 2*stock_spread and \
                    (benchmark or (np.sign(mavg_momentum[k]) != np.sign(mavg_momentum[k-1]) and mavg_momentum[k] < mavg_momentum[k-1])):
                entry_spread = spread[k]
                #d_position = -5
                d_position = -order_qty_base + int(-order_qty*(diff/std)**ORDER_POWER)
                d_position = max(d_position, -position-pos_limit/2)
                shorts[k] = entry_spread
                #print "tick", k, "cash -> short", curr_spread

            elif -diff >= entry_threshold*std and -diff >= 2*stock_spread and \
                    (benchmark or (np.sign(mavg_momentum[k]) != np.sign(mavg_momentum[k-1]) and mavg_momentum[k] > mavg_momentum[k-1])):
                entry_spread = spread[k]
                #d_position = 5
                d_position = order_qty_base + int(order_qty*(-diff/std)**ORDER_POWER)
                d_position = min(d_position, pos_limit/2-position)
                longs[k] = entry_spread
                #print "tick", k, "cash -> long", curr_spread


        if position < 0:
            #if (diff <= exit_threshold*std and mavg_momentum[k] >= momentum_threshold):
            #if (curr_spread-entry_spread > 2.0*stock_spread and diff <= exit_threshold*std and mavg_momentum[k] >= momentum_threshold):
                #position = "cash"
                #print "short -> cash profit"
            if (not ENSURE_MIN_SPREAD_BUYBACK or entry_spread-spread[k] >= 2*stock_spread) and \
                    diff <= exit_threshold*std and \
                    (benchmark or (np.sign(mavg_momentum[k]) != np.sign(mavg_momentum[k-1]) and mavg_momentum[k] > mavg_momentum[k-1])):
                d_position = -position
                longs[k] = curr_spread
                #print "tick", k, "short -> cash profit", curr_spread

                #if -diff >= entry_threshold*std >= 2.0*stock_spread:
                #    d_position += int(order_qty*(diff/std))

                n_profitable += 1

                if -diff >= entry_threshold*std >= 2*stock_spread and \
                    (benchmark or (np.sign(mavg_momentum[k]) != np.sign(mavg_momentum[k-1]) and mavg_momentum[k] > mavg_momentum[k-1])):
                    entry_spread = spread[k]
                    #d_position = 5
                    d_position2 = order_qty_base + int(order_qty*(-diff/std)**ORDER_POWER)
                    d_position2 = min(d_position2, pos_limit/2)
                    longs[k] = entry_spread
                    #print "tick", k, "cash -> long", curr_spread
                    d_position += d_position2


        elif position > 0:
            #if (-diff <= exit_threshold*std and mavg_momentum[k] <= -momentum_threshold):
            #if (curr_spread-entry_spread > 2.0*stock_spread and diff >= exit_threshold*std and mavg_momentum[k] <= -momentum_threshold):
                #position = "cash"
                #print "long -> cash profit"

            if (not ENSURE_MIN_SPREAD_BUYBACK or (spread[k]-entry_spread) >= 2*stock_spread) \
                    and -diff <= exit_threshold*std and \
                    (benchmark or (np.sign(mavg_momentum[k]) != np.sign(mavg_momentum[k-1]) and mavg_momentum[k] < mavg_momentum[k-1])):
                d_position = -position
                shorts[k] = curr_spread
                #print "tick", k, "long -> cash profit", curr_spread

                #if diff >= entry_threshold*std >= 2.0*stock_spread:
                #    d_position += int(-order_qty*(diff/std))

                n_profitable += 1

                if diff >= entry_threshold*std >= 2*stock_spread and \
                    (benchmark or (np.sign(mavg_momentum[k]) != np.sign(mavg_momentum[k-1]) and mavg_momentum[k] < mavg_momentum[k-1])):
                    entry_spread = spread[k]
                    #d_position = -5
                    d_position2 = -order_qty_base + int(-order_qty*(diff/std)**ORDER_POWER)
                    d_position2 = max(d_position2, -pos_limit/2)
                    shorts[k] = entry_spread
                    #print "tick", k, "cash -> short", curr_spread
                    d_position += d_position2


        #print k, spread[k]
        if (k == len(spread)-1):
            d_position = -position
         
        pnl_prev = pnl

        if abs(2*(d_position+position)) > pos_limit:
            raise Exception("FUCK YOU")

        position += d_position
        cash -= d_position*curr_spread
        cash -= abs(d_position)

        pnl = position*curr_spread + cash

        positions.append(2*position)

        #print holdings

        pnlarray.append(pnl)
        #print k, position, pnl
        if (k == len(spread)-1):
            diff = pnl-pnl_prev
            if(diff > 0):
                n_profitable += 1
            else:
                n_losses += 1
            print "pnl:", pnl, "good trades", n_profitable, "bad trades", n_losses, "total trades", n_profitable+n_losses
        
    trades = [longs, shorts]
    return pnl, trades, threshold_series, positions

#@TODO
def generateBacktests():
    print "foo"

def generateThresholds():
    thresholds = []
    for i in xrange(0, 15):
        for j in xrange(0, 5):
            for k in xrange(0, 15):
                thresholds.append([i, j, k])      


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

    
def graph(spread, mavgs, trades, pnlarray, threshold_series, positions):
    slow_mavg = mavgs[0]
    fast_mavg = mavgs[1]
    mavg_momentum = mavgs[2]
    '''Plot'''
    fig, axes = plt.subplots(nrows=4)
    #plt.plot(stock1, '-', stock2, '-', stock3, '-')
    axes[0].plot(map(lambda x: x+1 if not x is None else None, trades[0]), '^', ms = 8, color = 'g') # long
    axes[0].plot(map(lambda x: x-1 if not x is None else None, trades[1]), 'v', ms = 8, color = 'r') # short
    axes[0].plot(spread, '-')
    axes[0].plot(slow_mavg, '-')
    axes[0].plot(fast_mavg, '-')
    axes[0].plot(np.add(slow_mavg, threshold_series))
    axes[0].plot(np.subtract(slow_mavg, threshold_series))
    axes[1].plot(mavg_momentum, '-')
    axes[2].plot(pnlarray, '-')
    axes[3].plot(positions, "-")
    plt.show()

if __name__ == "__main__":
    #global pnl, entry_spread, curr_spread
    data = open("PairsRound1.csv", 'r')
    #data = open("PairsRound2.csv", 'r')
    #data = open("case_data.csv", 'r')
    #data = open("case_data2.csv", 'r')
    #data = open("case_data3.csv", 'r')
    #graphStocks(data)

    '''
    round 2
    0-1: adf=-0.217454948834, pvalue=0.936408799195, gamma=1.01102516423
    0-2: adf=-1.96598580138, pvalue=0.301683322768, gamma=0.987218706418
    1-2: adf=-0.508423561302, pvalue=0.890362186091, gamma=0.976328123767
    '''

    DO_ADF = False
    W = 1000
    if DO_ADF:
        prices = zip(*[map(float, line.split(",")) for line in data])
        a_series = []
        g_series = []
        for i in xrange(1, 100):
            adfs = []
            gammas = []
            for s1, s2 in [(0, 1), (0, 2), (1, 2)]:
                #adf, pvalue, _, _, _, _ = adfuller(np.subtract(prices[s1][i*10:i*10+W], prices[s2][i*10:i*10+W]))
                strt = max(0, i*10-W)
                end = i*10
                adf, pvalue, _, _, _, _ = adfuller(np.subtract(prices[s1][strt:end], prices[s2][strt:end]))
                adfs.append(adf)
                gamma = npla.lstsq(map(lambda p: [p], prices[s1][strt:end]), prices[s2][strt:end])[0][0]
                gammas.append(gamma)
                #print "{}-{}: adf={}, pvalue={}, gamma={}".format(s1, s2, adf, pvalue, gamma)
            a_series.append(adfs)
            g_series.append(gammas)
        fig = plt.figure()
        ax = fig.add_subplot(2, 1, 1)
        a1, a2, a3 = zip(*a_series)
        #a1, a2, a3 = zip(*g_series)
        ax.plot(a1)
        ax.plot(a2)
        ax.plot(a3)
        plt.show()
        exit()
    stocks = [0, 1]
    NO_STD = False
    pnlarray = []
    thresholds = [0.8, 0.6]  # entry_threshold, exit_threshold
    #thresholds = [3, 2]
    start = 50
    stock_spread = 1
    #stock_spread = 1.0
    order_qty = 1
    order_qty_base = 0
    fast_ema_alpha = 0.075
    #fast_ema_alpha = 0.5
    #fast_ema_alpha = 0.05
    mavg_windows = [500, 20, 20, 100]  # [slow_mavg_window, fast_mavg_window, momentum_window, std_window]
    spread, mavgs = getData(data, mavg_windows, stock1=stocks[0], stock2=stocks[1], alpha=fast_ema_alpha)
    #mavgs[0] = [0]*len(spread)
    pnl, trades, threshold_series, positions = backtest(spread, mavgs, thresholds, order_qty, pnlarray, mavg_windows, start, order_qty_base)
    #pnl, trades, threshold_series, positions = backtest(spread, mavgs, thresholds, order_qty, pnlarray, mavg_windows, 0, order_qty_base, benchmark=True)
    graph(spread, mavgs, trades, pnlarray, threshold_series, positions)

    '''
    Round 1
    thresholds = [1.0, 0.7] # entry_threshold, exit_threshold
    order_qty = 3
    mavg_windows = [500, 20, 20, 100] or 15 15? # [slow_mavg_window, fast_mavg_window, momentum_window, std_window]


    thresholds = [3, 2]
    start = 50
    stock_spread = 1.0
    order_qty = 1
    order_qty_base = 0
    fast_ema_alpha = 0.075
    #fast_ema_alpha = 0.05
    mavg_windows = [500, 20, 20, 100]  # [slow_mavg_window, fast_mavg_window, momentum_window, std_window]

    '''



