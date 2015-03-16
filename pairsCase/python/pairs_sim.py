from __future__ import division
import numpy as np
from scipy.stats import norm
from numpy.random import choice, normal
from random import sample
import matplotlib.pyplot as plt

case_file = open("case_data.csv", "w")


'''START PARAMETERS'''
ticks = 1000
number_of_securities = 3
number_of_pairs = 1

# noise parameters for cointegrated pairs
noise_drift = [0, 0, 0]
noise_vol = [0.02, 0.02, 0.02]

# GMB parameters if security is not in a pair
volatility = [0.02, 0.02, 0.02]
drift = [0, 0, 0]

# cointegration gamma, controls how strong each pair is cointegrated, should be between 0 and 1, recommend between 0.001 and 0.2
gamma = [0.015]

# cointegrating vectors
alpha = [(1.0, -1.0)]

# initial security values
S = [100.0, 100.0, 100.0]

'''END PARAMETERS'''

dW = {}

prices = [[s] for s in S]

dS = lambda i: drift[i]*S[i] + volatility[i]*S[i]*norm.rvs(loc=0, scale=1)

pairs_ = sample(np.arange(0, number_of_securities), 2*number_of_pairs)
rest = list(set(np.arange(0, number_of_securities)) - set(pairs_))
pairs = [(pairs_[2*i], pairs_[2*i+1]) for i in xrange(0, int(len(pairs_)/2))]

print "Correlated pairs are {}".format(pairs)

for _ in xrange(0, ticks):
    for j, (i1, i2) in enumerate(pairs):
        s1 = np.log(S[i1])
        s2 = np.log(S[i2])
        a = alpha[j]
        s1_ = s1 - gamma[j]*(s1 + (a[1]/a[0])*s2) + norm.rvs(loc=noise_drift[i1], scale=noise_vol[i1])
        s2_ = s2 - gamma[j]*(s2 + (a[0]/a[1])*s1) + norm.rvs(loc=noise_drift[i2], scale=noise_vol[i2])
        S[i1] = np.exp(s1_)
        S[i2] = np.exp(s2_)
        prices[i1].append(S[i1])
        prices[i2].append(S[i2])
    for i in rest:
        S[i] += dS(i)
        prices[i].append(S[i])
    case_file.write("{}\n".format(",".join(map(str, map(lambda x: round(x, 2), S)))))

case_file.close()

fig, axes = plt.subplots(nrows=2)

H = []
L = []

for i in xrange(0, number_of_securities):
    h, = axes[0].plot(np.arange(0, ticks+1), prices[i])
    H.append(h)
    L.append("{}".format(i))

axes[0].legend(H, L, loc=2)

H = []
L = []

for s1, s2 in pairs:
    h, = axes[1].plot(np.arange(0, ticks+1), np.subtract(prices[s1], prices[s2]))
    H.append(h)
    L.append("{}-{}".format(s1, s2))

axes[1].legend(H, L, loc=2)

plt.show()

