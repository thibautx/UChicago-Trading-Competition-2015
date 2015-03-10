import matplotlib.pyplot as plt
import numpy as np
import csv

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

if __name__ == "__main__":

	data = open("PairsRound1.csv", 'r')
	stock1 = []
	stock2 = []
	stock3 = []
	ratio = []
	spread = []
	x = [] # ratio 1
	y = []
	z = []
	ema = []

	window1 = 500
	window2 = 50
	count = 0;
	for line in data:
		#stock1.append(line.split(',')[0])
		#stock2.append(line.split(',')[1])
		stock1price = float(line.split(',')[0])
		stock2price = float(line.split(',')[1])
		#stock3price = float(line.split(',')[2])
		#ratio.append(stock1price/stock3price)
		spread.append(stock1price - stock2price)
		#ema.append()
		x.append(0)
		y.append(2)
		z.append(-2)

	mavg1 = []
	for i in xrange(1, window1):
		mavg1.append(movingaverage(spread[:i],i))
	mavg1.extend(movingaverage(spread, window1))

	mavg2 = []
	for i in xrange(1, window2):
		mavg2.append(movingaverage(spread[:i],i))
	mavg2.extend(movingaverage(spread, window2))


	#plt.plot(stock1, '-', stock2, '-')
	#plt.plot(ratio, '-')
	plt.plot(mavg1, '-')
	plt.plot(mavg2, '-')
	plt.plot(spread, '-')
	plt.plot(y, '-')
	plt.plot(z, '-')
	plt.plot(x, '-')
	plt.show()