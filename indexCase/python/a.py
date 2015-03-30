from __future__ import division
from random import randint
import numpy as np
import numpy.linalg as npla
import matplotlib.pyplot as plt

from sklearn.decomposition import PCA
from copy import deepcopy

from os import path


'''



'''

''' --- parameters --- '''
Z = 100
ROUND = 3
PLOT_BENCHMARK = False
OFFSET = 0000
WINDOW_LENGTH = 10000
substitution_window = 6     # tuned: round 1 - 5, round 2 - 7, round 3 - ?
buyback_window = 1
NO_T_COSTS = False
NO_BUYBACK = False
''' ------------------ '''

BASE_DIR = path.dirname(path.dirname(__file__))
DATA_DIR = path.join(BASE_DIR, "market-data")
ROUND_DIR = path.join(DATA_DIR, "round{}".format(ROUND))

data_file = path.join(ROUND_DIR, "prices.csv")
weights_file = path.join(ROUND_DIR, "capWeights.csv")
tradable_changes_file = path.join(ROUND_DIR, "tradable_changes.csv")
tradable_init_file = path.join(ROUND_DIR, "tradable_init.csv")

securities = [randint(0, 30), randint(0, 30)]

offset = OFFSET
window_length = WINDOW_LENGTH

start = 1 + offset
end = window_length + offset

prices = {sec: [] for sec in securities}
index_prices = []

weights = []

tradable = {}
cur_tradable = None

# initialize tradable dictionary
with open(tradable_init_file) as f:
    tradable[1] = {}
    for i, line in enumerate(f.readlines()):
        if int(line) == 1:
            tradable[1][i] = True
        else:
            tradable[1][i] = False

# create 2-level dictionary of tick mapping to security mapping to tradable
with open(tradable_changes_file) as f:
    last_tradable = tradable[1]
    for line in f.readlines():
        tick, sec, v = map(int, line.split(","))
        #tick += 20
        tradable[tick] = deepcopy(last_tradable)
        if v == 1:
            tradable[tick][sec] = True
        else:
            tradable[tick][sec] = False
        last_tradable = tradable[tick]

with open(weights_file) as f:
    for line in f.readlines():
        weight = float(line)
        weights.append(weight)


with open(data_file) as f:
    for i, line in enumerate(f.readlines()):
        if i == 0:
            continue
        vals = map(float, line.split(","))
        for k, sec in enumerate(securities):
            prices[sec].append(vals[sec])
        index_prices.append(vals[-1])


n = len(securities)
m = len(prices[securities[0]]) - 1
R = np.zeros((n, m))
Y = np.zeros((n, m))
for i, sec in enumerate(securities):
    R[i:] = np.diff(prices[sec]) / prices[sec][:-1]


means = []
stds = []   # hehe


for i, sec in enumerate(securities):
    R_mean = np.average(R[i, :])
    R_std = np.std(R[i, :])
    means.append(R_mean)
    stds.append(R_std)
    Y[i:] = (R[i, :] - R_mean) / R_std


c_series = []
c2_series = []

for i in xrange(0, 10000-10*Z):
    P = np.corrcoef(Y[:, i:i+Z], Y[:, i:i+Z])
    ZZ = 10*Z
    P2 = np.corrcoef(Y[:, i:i+ZZ], Y[:, i:i+ZZ])
    c_series.append(P[0, 1])
    c2_series.append(P2[0, 1])


fig = plt.figure()
ax = fig.add_subplot(2, 1, 1)
h1, = ax.plot(c_series)
h2, = ax.plot(c2_series)

ax.legend([h1, h2], ['{}-tick corr'.format(Z), '{}-tick corr'.format(ZZ)])

print securities

plt.show()