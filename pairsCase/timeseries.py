import matplotlib.pyplot as plt
import numpy as np
import csv

data = open("PairsRound2.csv", 'r')

stock1 = []
stock2 = []
spread = []
x = []

for line in data:
	#stock1.append(line.split(',')[0])
	#stock2.append(line.split(',')[1])
	stock1price = float(line.split(',')[0])
	stock2price = float(line.split(',')[1])
	spread.append(stock1price/stock2price)
	x.append(1)

#plt.plot(stock1, '-', stock2, '-')
plt.plot(spread, '-')
plt.plot(x, '-')
plt.show()