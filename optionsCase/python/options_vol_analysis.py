import matplotlib.pyplot as plt
import numpy as np

output_file = open('output.txt')
vol_file = open('vol_data.txt')

true_vol_series = [float(v) for v in vol_file.readlines()]

estimate_vol_series = []
pnl_series = []
vega_series = []

for line in output_file.readlines():
    if line[:6] == "Vol = ":
        vol = float(line[6:])
        estimate_vol_series.append(vol)
    elif line[:6] == "PnL = ":
        pnl = float(line[6:])
        pnl_series.append(pnl)
    elif line[:7] == "Vega = ":
        vega = float(line[7:])
        vega_series.append(vega)

output_file.close()
vol_file.close()

fig, axes = plt.subplots(nrows=3)
#ax = fig.add_subplot(2, 1, 1)

L = len(true_vol_series)

h1, = axes[0].plot(np.arange(0, L), true_vol_series)
h2, = axes[0].plot(np.arange(0, L), estimate_vol_series)
h3, = axes[1].plot(np.arange(0, L), pnl_series)
h4, = axes[2].plot(np.arange(0, L), vega_series)

axes[0].legend([h1, h2], ['true', 'guess'])
axes[1].legend([h3], ['pnl'])
axes[2].legend([h4], ['vega'])

plt.show()

