import numpy as np
import matplotlib.pyplot as plt
from os import path

data_file = "C:\\Users\\Greg Pastorek\\Documents\\FEC\\uchicago-algo\\indexCase\\market-data\\round1\\prices.csv"

ROUND = 1

BASE_DIR = path.dirname(path.dirname(__file__))
DATA_DIR = path.join(BASE_DIR, "market-data")
ROUND_DIR = path.join(DATA_DIR, "round{}".format(ROUND))

data_file = path.join(ROUND_DIR, "prices.csv")
weights_file = path.join(ROUND_DIR, "capWeights.csv")
tradable_changes_file = path.join(ROUND_DIR, "tradable_changes.csv")
tradable_init_file = path.join(ROUND_DIR, "tradable_init.csv")

# note, index is 30
#securities = np.concatenate([np.arange(0, 5), [30]])
securities = [30]

plot_start = 1
plot_end = 10000

prices = {sec: [] for sec in securities}

with open(data_file) as f:
    for i, line in enumerate(f.readlines()):
        if i >= plot_start and i <= plot_end:
            vals = map(float, line.split(","))
            for sec in securities:
                prices[sec].append(vals[sec])


weights = []

with open(weights_file) as f:
    for line in f.readlines():
        weight = float(line)
        weights.append(weight)


ban_weights = []
banned_secs = {}

# create 2-level dictionary of tick mapping to security mapping to tradable
with open(tradable_changes_file) as f:
    for line in f.readlines():
        tick, sec, v = map(int, line.split(","))
        if v == 0 and not sec in banned_secs:
            banned_secs[sec] = True
            ban_weights.append(weights[sec])

ban_weights = np.array(ban_weights)

fig = plt.figure()
ax = fig.add_subplot(2, 1, 1)

H = []
L = []

index_prices = prices[30]

v1 = np.sum(np.log(np.divide(index_prices[1:], index_prices[:-1]))**2)

print len(banned_secs)

print v1

v2 = 2*60*np.sum((np.exp(ban_weights/60) - 1))

v3 = 2*np.sum((np.exp(ban_weights) - 1))

print v2
print v3
print v1 + v2

for sec in securities:
    h, = ax.plot(prices[sec])
    H.append(h)
    L.append(str(sec))

box = ax.get_position()
ax.set_position([box.x0, box.y0, box.width * 0.8, box.height])

ax.legend(H, L, loc='center left', bbox_to_anchor=(1, 0.5))



plt.show()