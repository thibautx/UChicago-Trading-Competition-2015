from __future__ import division
import numpy as np
from scipy.stats import norm
from numpy.random import choice, normal
import matplotlib.pyplot as plt

case_file = open("case_data.csv", "w")
vol_file = open("vol_data.txt", "w")

case_file.write("Direction,Strike,Price\n")

def callPrice(K, S, t, r, v):
    d1 = 1/(v*np.sqrt(t)) * (np.log(S/K) + (r + (v**2)/2)*t)
    d2 = d1 - v*np.sqrt(t)
    return norm.cdf(d1)*S - norm.cdf(d2)*K*np.exp(-r*t)

r = 0.01
t = 1
S = 100

v = 0.3
v_vol = 0.05
v_drift = 0

directions = np.array([-1, 1])
strikes = np.array([80, 90, 100, 110, 120])

edge = 0.05
noise_vol = 0.05**2
noise_mean = 1.0

ticks = 100


V = []

for _ in xrange(0, ticks):
    direction = choice(directions)
    strike = choice(strikes)
    v += v_vol * v * norm.rvs()
    e = 1+edge if direction == -1 else 1-edge
    noise = norm.rvs(loc=noise_mean, scale=np.sqrt(noise_vol))
    price = callPrice(strike, S, t, r, v) * e * noise
    case_file.write("{},{},{}\n".format(direction, strike, price))
    vol_file.write("{}\n".format(v))
    V.append(v)

case_file.close()
vol_file.close()

fig = plt.figure()
ax = fig.add_subplot(2, 1, 1)

ax.plot(np.arange(0, ticks), V)

plt.show()

