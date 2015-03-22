import numpy as np
import numpy.linalg as npla
import matplotlib.pyplot as plt

from sklearn.decomposition import PCA
from copy import deepcopy

# -0.115153840366
# -0.113153840366

DUMB_MODE = True
REBALANCE_SUB_SUBBED = True
REBALANCE_REENTRY = True

n_components = 15

data_file = "C:\\Users\\Greg Pastorek\\Documents\\FEC\\uchicago-algo\\indexCase\\market-data\\round1\\prices.csv"
weights_file = "C:\\Users\\Greg Pastorek\\Documents\\FEC\\uchicago-algo\\indexCase\\market-data\\round1\\capWeights.csv"
tradable_changes_file = "C:\\Users\\Greg Pastorek\\Documents\\FEC\\uchicago-algo\\indexCase\\market-data\\round1\\tradable_changes.csv"
tradable_init_file = "C:\\Users\\Greg Pastorek\\Documents\\FEC\\uchicago-algo\\indexCase\\market-data\\round1\\tradable_init.csv"


# note, index is 31
# securities = np.concatenate([np.arange(0, 5), [30]])
securities = np.arange(0, 30)

plot_start = 1
plot_end = 1000
offset = 0000

plot_start += offset
plot_end += offset

prices = {sec: [] for sec in securities}
index_prices = []

weights = []

tradable = {}
cur_tradable = None

with open(tradable_init_file) as f:
    tradable[1] = {}
    for i, line in enumerate(f.readlines()):
        if int(line) == 1:
            tradable[1][i] = True
        else:
            tradable[1][i] = True

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
        if i >= plot_start and i <= plot_end:
            vals = map(float, line.split(","))
            for k, sec in enumerate(securities):
                #w = weights[sec]
                prices[sec].append(vals[sec])
            index_prices.append(vals[-1])

n = len(securities)
m = len(prices[0]) - 1
R = np.zeros((n, m))
Y = np.zeros((n, m))
for i, sec in enumerate(securities):
    R[i:] = np.diff(prices[sec]) / prices[sec][:-1]

means = []
stds = []

for i, sec in enumerate(securities):
    R_mean = np.average(R[i, :])
    R_std = np.std(R[i, :])
    means.append(R_mean)
    stds.append(R_std)
    Y[i:] = (R[i, :] - R_mean) / R_std

P = np.corrcoef(Y, Y)[:n, :n]

#for i in xrange(0, 30):
#    P[i, i] = 0

E = sorted(zip(*npla.eig(P)), key=lambda x: x[0], reverse=True)

evals, evects = zip(*E)


Q = np.zeros((30, 30))

for i, vect in enumerate(evects):
    for j in xrange(0, len(vect)):
        if vect[j] > 0:
            Q[i, j] = vect[j] / stds[j]




myweights = np.zeros(len(evects[0]))
for q in Q[:]:
    #print q
    #myweights += q / npla.norm(q)
    myweights += q

#myweights = np.ones(30)

def compute_score(DUMB_MODE=False):

    K = 1

    index_s = []
    est_s = []

    myweights = np.copy(weights)

    last_substitutions = np.diag(weights)

    with open(data_file) as f:
        for i, line in enumerate(f.readlines()):
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

                    sub_ind = np.argmax(last_substitutions[sec, :])

                    if last_substitutions[sec, sub_ind] == 0:
                        raise Exception("2 - No nonzero sub weight found for {}".format(sec))

                    # k * p_sub * w_sub = p_lsub * w_sec_lsub
                    sub_weight = last_substitutions[sec, sub_ind] * vals[sub_ind] / vals[substitute]
                    myweights[substitute] += sub_weight
                    substitutions[sec, substitute] = sub_weight

                    if substitutions[sec, substitute] == 0:
                        raise Exception("4 - computed a zero sub_weight")

                    if sec != substitute:
                        myweights[sec] = 0

                last_substitutions = np.copy(substitutions)

                if DUMB_MODE:
                    z = len(filter(lambda x: x > 0, myweights)) / 30.0
                    myweights = np.array(map(lambda x: 1/z if x > 0 else 0, myweights))

            if i >= plot_start and i <= plot_end:
                vals = map(float, line.split(","))
                index = index_prices[i-1-offset]
                est = np.dot(vals[:-1], myweights) / K
                if K == 1:
                    K = est / index
                    est /= K
                #print est / index
                index_s.append(index)
                est_s.append(est)


    index_returns = np.array(map(np.log, np.divide(index_s[1:], index_s[:-1])))
    est_returns = np.array(map(np.log, np.divide(est_s[1:], est_s[:-1])))

    returns_diff = index_returns - est_returns

    score = [-returns_diff[0]**2]

    for rd in returns_diff[1:]:
        score.append(score[-1] - rd**2)

    return index_s, est_s, score

# print P


m = 0
im = 0
jm = 0
for i in xrange(0, 30):
    for j in xrange(0, 30):
        if P[i, j] != 1.0:
            if P[i, j] > m:
                m = P[i, j]
                im = i
                jm = j
            m = max(P[i, j], m)

#print m, im, jm

#pca = PCA(n_components=n_components)

#pca.fit(P)


index_s, est_s, score = compute_score(DUMB_MODE=False)
_, _, benchmark = compute_score(DUMB_MODE=False)

#ax = fig.add_subplot(2, 1, 1)
fig, axes = plt.subplots(nrows=2)

h1, = axes[0].plot(index_s)
h2, = axes[0].plot(est_s)

h3, = axes[1].plot(score)
h4, = axes[1].plot(benchmark)

box = axes[0].get_position()
axes[0].set_position([box.x0, box.y0, box.width * 0.8, box.height])

axes[0].legend([h1, h2], ['index', 'portfolio'], loc='center left', bbox_to_anchor=(1, 0.5))

box = axes[1].get_position()
axes[1].set_position([box.x0, box.y0, box.width * 0.8, box.height])
axes[1].legend([h3, h4], ['score', 'benchmark'], loc='center left', bbox_to_anchor=(1, 0.5))

print score[-1]

plt.show()