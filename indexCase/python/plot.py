import numpy as np
import matplotlib.pyplot as plt


data_file = "C:\\Users\\Greg Pastorek\\Documents\\FEC\\uchicago-algo\\indexCase\\market-data\\round1\\prices.csv"

# note, index is 31
#securities = np.concatenate([np.arange(0, 5), [30]])
securities = [13, 15]

plot_start = 1
plot_end = 2000

prices = {sec: [] for sec in securities}

with open(data_file) as f:
    for i, line in enumerate(f.readlines()):
        if i >= plot_start and i <= plot_end:
            vals = map(float, line.split(","))
            for sec in securities:
                prices[sec].append(vals[sec])


fig = plt.figure()
ax = fig.add_subplot(2, 1, 1)

H = []
L = []

for sec in securities:
    h, = ax.plot(prices[sec])
    H.append(h)
    L.append(str(sec))

box = ax.get_position()
ax.set_position([box.x0, box.y0, box.width * 0.8, box.height])

ax.legend(H, L, loc='center left', bbox_to_anchor=(1, 0.5))



plt.show()