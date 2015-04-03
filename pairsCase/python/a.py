import numpy as np
import matplotlib.pyplot as plt

filepath = "C:\\Users\\Greg Pastorek\\Documents\\FEC\uchicago-algo\\pairsCase\\python\\PairsRound2.csv"

num_securities = 2
securities = [[], [], []]

with open(filepath) as f:
    lines = f.readlines()

for line in lines:
    line_split = line.split(",")
    for i, val_str in enumerate(line_split):
        val = float(val_str)
        securities[i].append(val)

for i in xrange(0, num_securities):
    d = np.diff(securities[i]) / securities[i][:-1]
    std = np.std(d)
    mean = np.average(d)
    print std, mean

#fig = plt.figure()
#ax = fig.add_subplot(2, 1, 1)

fig, axes = plt.subplots(nrows=2)

H = []
L = []

for i, sec in enumerate(securities):
    h, = axes[0].plot(sec)
    H.append(h)
    L.append(i)

axes[0].legend(H, L)
axes[1].plot(np.diff(np.subtract(securities[0], securities[1])))


plt.show()

