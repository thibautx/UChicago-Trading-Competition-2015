from __future__ import division
import numpy as np
import numpy.linalg as npla
import matplotlib.pyplot as plt

from sklearn.decomposition import PCA
from copy import deepcopy

from os import path


import time

o = open("output.txt", "w")

t1 = time.time()

''' --- parameters --- '''
ROUND = 2
PLOT = True
RUN_BENCHMARK = False
WINDOW_LENGTH = 10000
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

securities = np.arange(0, 30)

window_length = WINDOW_LENGTH

price_data = []
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
        # tick += 20
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
        price_data.append(vals)


n = len(securities)
m = len(prices[0]) - 1
R = np.zeros((n, m))
Y = np.zeros((n, m))
for i, sec in enumerate(securities):
    #R[i:] = np.diff(prices[sec]) / prices[sec][:-1]
    R[i:] = np.log(np.array(prices[sec][1:]) / np.array(prices[sec][:-1]))

means = []
stds = []  # hehe

for i, sec in enumerate(securities):
    R_mean = np.average(R[i, :])
    R_std = np.std(R[i, :])
    means.append(R_mean)
    stds.append(R_std)
    #Y[i, :] = (R[i, :] - R_mean) / R_std
    Y[i, :] = R[i, :]




# dumb_mode simply evenly distributes all the weights
def compute_score(data, mode=False, hist_weight=1.0, offset=0):
    P_hist = np.corrcoef(Y, Y)[:n, :n]
    P = np.copy(P_hist)
    P2 = np.copy(P_hist)
    P3 = np.copy(P_hist)

    start = offset + 1
    end = offset + WINDOW_LENGTH

    index_s = []
    est_s = []
    ret_s = []
    p_s = []

    myweights = np.copy(weights)

    t_cost_series = [0]

    last_vals = None
    first_val = None
    cur_tradable = None
    lcur_tradable = tradable[1]

    transitions = []
    cur_subs = {s: {'sec': s, 'sub': s, 'remaining': 0, 'transaction': {}} for s in securities}

    for i in xrange(1, start):
        if i in tradable:
            cur_tradable = tradable[i]

    for tick, vals in enumerate(data):
        #f = open(data_file)

        #for i, line in enumerate(f.readlines()):

        #if i == 0:
        #    continue

        #vals = map(float, line.split(","))
        i = tick + start
        last_weights = np.copy(myweights)

        if i in tradable:
            cur_tradable = tradable[i]

        if not last_vals:
            last_vals = vals
        if not first_val:
            first_val = np.dot(weights, vals[:-1])

        # if we are at a tradable change, make adjustments
        if i in tradable or i == start:

            if i >= min_corr_window + start:
                i_s = start
                P = np.corrcoef(Y[:, i_s:i], Y[:, i_s:i])[:n, :n]

            if lcur_tradable and i > start and i <= end:
                for sec in lcur_tradable:
                    if not lcur_tradable[sec] and last_weights[sec] > 1e-10:
                        pass
                        #print i, sec, last_weights[sec]
                        #raise Exception("Penalty")

            lcur_tradable = cur_tradable

            for sec in securities:

                if cur_tradable[cur_subs[sec]['sub']] and not cur_tradable[sec]:
                    continue

                Pc = hist_weight*P_hist + (1-hist_weight)*P

                substitute = np.argmax(Pc[sec])

                while (not cur_tradable[substitute]):
                    Pc[sec, substitute] = -np.inf
                    substitute = np.argmax(Pc[sec])

                if cur_subs[sec]['sub'] != substitute:
                    nadds = 1 if i == start or sec == substitute else substitution_window
                    rem = 1 if i == start else 20
                    #print "{} subs for {} and covers {}".format(substitute, cur_subs[sec]['sub'], sec)
                    t = {
                        'sec': cur_subs[sec]['sub'],
                        'sub': substitute,
                        'remaining': rem,
                        'value': weights[sec] / nadds
                    }
                    transitions.append(t)
                    cur_subs[sec] = {
                        'sub': substitute,
                        'remaining': rem,
                        'transaction': t
                    }

        for t in np.copy(transitions):
            sec = t['sec']
            sub = t['sub']
            w = t['value']
            t['remaining'] -= 1
            r = t['remaining']

            if r < substitution_window:
                #print "Transferring {} from {} to {}".format(round(w, 6), sec, sub)
                myweights[sub] += w
                myweights[sec] -= w

            if sec in cur_subs:
                cur_subs[sec]['remaining'] -= 1

            if r == 0:
                transitions.remove(t)

        if mode == 'dumb':
            z = len(filter(lambda x: x > 0, myweights)) / 30.0
            myweights = np.array(map(lambda x: 1 / z if x > 0 else 0, myweights))

        index = index_prices[i - 1]

        # print len([1 for c in cur_tradable if cur_tradable[c] == True])
        if abs(np.sum(myweights) - 1.0) > 1e-10:
            raise Exception(
                "Weights don't sum to 1.0 go fuck yourself - got error {}".format(np.sum(myweights) - 1.0))

        last_est = np.dot(last_vals[:-1], myweights)
        est = np.dot(vals[:-1], myweights)
        p_s.append(est)
        o.write(",".join(map(str, myweights)) + "\n")
        ret = est - last_est
        est /= last_est

        X = 1
        transaction_cost = -1 * np.sum(np.exp(np.abs(myweights - last_weights) / X) - 1) * X / 200.0
        if NO_T_COSTS:
            transaction_cost = 0

        if i > start:
            t_cost_series.append(transaction_cost + t_cost_series[-1])

        index_s.append(index)
        est_s.append(est)
        ret_s.append(ret)
        last_vals = vals

    index_returns = np.array(map(np.log, np.divide(index_s[1:], index_s[:-1])))
    # est_returns = np.array(map(np.log, np.divide(est_s[1:], est_s[:-1])))
    est_returns = np.array(map(np.log, est_s))

    #print est_returns

    returns_diff = index_returns - est_returns[:-1]

    #score = [-returns_diff[0] ** 2]
    score = [-7.096271478469292E-6]

    for i, rd in enumerate(returns_diff[1:]):
        print "{} --- r_diff={}".format(i+2, rd**2)
        #print "i_r={}".format(index_returns[i+1])
        #print "p_r={}".format(est_returns[i+1])
        #print "i={}".format(index_s[i+2])
        #print "p={}".format(p_s[i+2])
        #print "score={}".format(score[-1] - rd ** 2)
        score.append(score[-1] - rd ** 2)

    portfolio_s = [first_val]

    for r in ret_s[1:]:
        portfolio_s.append(r + portfolio_s[-1])

    return np.array(index_s), np.array(portfolio_s), np.array(score), np.array(t_cost_series[1:])


def test(offset, hist_weight):
    data = price_data[offset+1:offset+WINDOW_LENGTH+1]
    index_s, est_s, score, t_costs = compute_score(data, mode='normal', hist_weight=hist_weight, offset=offset)

    if PLOT:
        print score[-1]
        print t_costs[-1]
        print score[-1] + t_costs[-1]

    if PLOT:
        # ax = fig.add_subplot(2, 1, 1)
        fig, axes = plt.subplots(nrows=2)

        h1, = axes[0].plot(index_s)
        h2, = axes[0].plot(est_s)

        h3, = axes[1].plot(score)
        h4, = axes[1].plot(t_costs)
        h5, = axes[1].plot(score + t_costs)
        H = [h3, h4, h5]
        L = ["score", "t cost", "total"]

    if RUN_BENCHMARK:
        bscore, btcosts, benchmark, t_costs = compute_score(data, mode='normal', hist_weight=1.0, offset=offset)
        if PLOT:
            h6, = axes[1].plot(benchmark + t_costs)
            h7, = axes[1].plot(benchmark)
            H.append(h6)
            L.append("benchmark")
            H.append(h7)
            L.append("benchmark score")

    if PLOT:
        box = axes[0].get_position()
        axes[0].set_position([box.x0, box.y0, box.width * 0.8, box.height])

        axes[0].legend([h1, h2], ['index', 'portfolio'], loc='center left', bbox_to_anchor=(1, 0.5))

        box = axes[1].get_position()
        axes[1].set_position([box.x0, box.y0, box.width * 0.8, box.height])
        axes[1].legend(H, L, loc='center left', bbox_to_anchor=(1, 0.5))

    t2 = time.time()

    #print "Took {} seconds".format(t2-t1)

    if PLOT:
        plt.show()

    if not RUN_BENCHMARK:
        benchmark = [0]

    return score[-1] + t_costs[-1], benchmark[-1] + t_costs[-1]

'''--- tunable parameters ---'''
substitution_window = 1   # tuned: round 1 - 5, round 2 - 7, round 3 - 15
buyback_window = 1
min_corr_window = 50
HIST_WEIGHT = 1.0
'''--------------------------'''

scores = []
bm_scores = []
score_diffs = []

'''
p = np.corrcoef(Y, Y)[:n, :n]
o_str = "{"
for row in p:
    o_str += "\t{" + ",".join(map(str, row)) + "},\n"
o_str = o_str[:-2] + "\n};"
print o_str
exit()
'''

for i in xrange(0, 1):
    score, bm_score = test(i*1000, HIST_WEIGHT)
    scores.append(score)
    bm_scores.append(bm_score)
    score_diffs.append(score-bm_score)

print (ROUND, substitution_window, buyback_window, min_corr_window, HIST_WEIGHT)
print "Average score = {}, {}".format(np.average(scores), np.std(scores))
print "Average BM score = {}, {}".format(np.average(bm_scores), np.std(bm_scores))
print "Average score difference = {}, {}".format(np.average(score_diffs), np.std(score_diffs))


'''
ROUND 1!!!!!!!!!!!
(1, 1, 1, 50, 0.8)
Average score = -0.0312375559848, 0.0254947942165
Average BM score = -0.031964840644, 0.0251552871856
Average score difference = 0.000727284659192, 0.00440601879265

ROUND 2!!!!!!!!!!!
(2, 7, 1, 50, 0.3)
Average score = -0.0170022632532, 0.00671048744717
Average BM score = -0.0173139792145, 0.00664535510529
Average score difference = 0.000311715961374, 0.000967051746518


ROUND 3!!!!!!!!!!!
(3, 8, 1, 50, 0.4)
Average score = -0.0897718377963, 0.0851056307408
Average BM score = -0.0928118714829, 0.0838844301628
Average score difference = 0.00304003368662, 0.0075270901153


'''