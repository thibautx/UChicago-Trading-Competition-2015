import matplotlib.pyplot as plt
import numpy as np
import csv

data = open("PairsRound2.csv", 'r')

stock1 = []
stock2 = []

for line in data:
	stock1.append(line.split(',')[0])
	stock2.append(line.split(',')[1])

plt.plot(stock1, '-', stock2, '-')
plt.show()