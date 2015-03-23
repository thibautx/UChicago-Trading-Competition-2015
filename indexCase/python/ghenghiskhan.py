import numpy as np
import numpy.linalg as npla
import matplotlib.pyplot as plt

from sklearn.decomposition import PCA
from copy import deepcopy

from os import path


''' --- parameters --- '''

ROUND = 1
PLOT_BENCHMARK = False
OFFSET = 2000
WINDOW_LENGTH = 1000
BOOBS = 3.153402393209 / 1

''' ------------------ '''

BASE_DIR = path.dirname(path.dirname(__file__))
DATA_DIR = path.join(BASE_DIR, "market-data")
ROUND_DIR = path.join(DATA_DIR, "round{}".format(ROUND))

data_file = path.join(ROUND_DIR, "prices.csv")
weights_file = path.join(ROUND_DIR, "capWeights.csv")
tradable_changes_file = path.join(ROUND_DIR, "tradable_changes.csv")
tradable_init_file = path.join(ROUND_DIR, "tradable_init.csv")

securities = np.arange(0, 30)

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
m = len(prices[0]) - 1
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


P = np.corrcoef(Y, Y)[:n, :n]


# dumb_mode simply evenly distributes all the weights
def compute_score(mode=False):

    K = 1

    index_s = []
    est_s = []

    myweights = np.copy(weights)

    last_substitutions = np.diag(weights)

    t_cost_series = [0]

    with open(data_file) as f:
        for i, line in enumerate(f.readlines()):
            last_weights = myweights
            if i >= start and i <= end:
                # if we are at a tradable change, make adjustments
                if i in tradable:
                    vals = map(float, line.split(","))
                    myweights = np.zeros(30)
                    cur_tradable = tradable[i]
                    substitutions = np.zeros((30, 30))

                    for sec in securities:

                        Pc = np.copy(P)
                        substitute = np.argmax(Pc[sec])

                        while not cur_tradable[substitute]:
                            Pc[sec, substitute] = 0
                            substitute = np.argmax(Pc[sec])
                            if mode == 'random':
                                if substitute != sec:
                                    substitute = sec
                                    while not cur_tradable[substitute]:
                                        substitute = np.random.randint(0, high=30)

                        sub_ind = np.argmax(last_substitutions[sec, :])

                        if last_substitutions[sec, sub_ind] == 0:
                            raise Exception("2 - No nonzero sub weight found for {}".format(sec))

                        # k * p_sub * w_sub = p_lsub * w_sec_lsub
                        sub_weight = last_substitutions[sec, sub_ind] * vals[sub_ind] / vals[substitute]

                        if sub_weight > BOOBS:
                            b = int(sub_weight / BOOBS) + 1

                            for _ in xrange(0, b-1):
                                sub_weight /= b
                                sub_weight = 0
                                myweights[substitute] += sub_weight
                                substitutions[sec, substitute] = sub_weight
                                Pc[sec, substitute] = 0
                                substitute = np.argmax(Pc[sec])

                                while not cur_tradable[substitute]:
                                    Pc[sec, substitute] = 0
                                    substitute = np.argmax(Pc[sec])
                                    if mode == 'random':
                                        if substitute != sec:
                                            substitute = sec
                                            while not cur_tradable[substitute]:
                                                substitute = np.random.randint(0, high=30)

                                sub_ind = np.argmax(last_substitutions[sec, :])

                                if last_substitutions[sec, sub_ind] == 0:
                                    raise Exception("2 - No nonzero sub weight found for {}".format(sec))

                                # k * p_sub * w_sub = p_lsub * w_sec_lsub
                                sub_weight = last_substitutions[sec, sub_ind] * vals[sub_ind] / vals[substitute]
                                #sub_weight /= b


                        myweights[substitute] += sub_weight
                        substitutions[sec, substitute] = sub_weight

                        if substitutions[sec, substitute] == 0:
                            raise Exception("4 - computed a zero sub_weight")

                        if sec != substitute:
                            myweights[sec] = 0

                    last_substitutions = np.copy(substitutions)

                    if mode == 'dumb':
                        z = len(filter(lambda x: x > 0, myweights)) / 30.0
                        myweights = np.array(map(lambda x: 1/z if x > 0 else 0, myweights))

                vals = map(float, line.split(","))
                index = index_prices[i-1]

                est = np.dot(vals[:-1], myweights / K)

                #if i == 100:
                #    print myweights - last_weights
                transaction_cost2 = -20 * np.sum(np.exp(np.abs(myweights - last_weights) / 20) - 1)
                transaction_cost = -1 * np.sum(np.exp(np.abs(myweights - last_weights)) - 1)

                #if transaction_cost < transaction_cost2:
                #    raise Exception("Fuck you")

                t_cost_series.append(transaction_cost + t_cost_series[-1])

                # at first tick adjust K so that the prices are alligned
                if K == 1:
                    K = est / index
                    est /= K
                index_s.append(index)
                est_s.append(est)


    index_returns = np.array(map(np.log, np.divide(index_s[1:], index_s[:-1])))
    est_returns = np.array(map(np.log, np.divide(est_s[1:], est_s[:-1])))

    returns_diff = index_returns - est_returns

    score = [0, -returns_diff[0]**2]

    for rd in returns_diff[1:]:
        score.append(score[-1] - rd**2)

    return np.array(index_s), np.array(est_s), np.array(score), np.array(t_cost_series[1:])


index_s, est_s, score, t_costs = compute_score(mode='normal')

#ax = fig.add_subplot(2, 1, 1)
fig, axes = plt.subplots(nrows=2)

h1, = axes[0].plot(index_s)
h2, = axes[0].plot(est_s)

h3, = axes[1].plot(score)
h4, = axes[1].plot(t_costs)
h5, = axes[1].plot(score+t_costs)
H = [h3, h4, h5]
L = ["score", "t cost", "total"]

if PLOT_BENCHMARK:
    _, _, benchmark, t_costs = compute_score(mode='random')
    h6, = axes[1].plot(benchmark+t_costs)
    H.append(h6)
    L.append("benchmark")

box = axes[0].get_position()
axes[0].set_position([box.x0, box.y0, box.width * 0.8, box.height])

axes[0].legend([h1, h2], ['index', 'portfolio'], loc='center left', bbox_to_anchor=(1, 0.5))

box = axes[1].get_position()
axes[1].set_position([box.x0, box.y0, box.width * 0.8, box.height])
axes[1].legend(H, L, loc='center left', bbox_to_anchor=(1, 0.5))

print score[-1]

plt.show()