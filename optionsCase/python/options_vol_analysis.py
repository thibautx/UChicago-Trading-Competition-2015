import matplotlib.pyplot as plt
import numpy as np
import numpy.linalg as npla

#PLOT_PRICE = True
PLOT_PRICE = False

def analyze(show_plot=True):
    output_file = open('output.txt')
    vol_file = open('vol_data.txt')

    true_vol_series = []
    #true_vol_series = [float(v) for v in vol_file.readlines()]

    estimate_vol_series = []
    pnl_series = []
    vega_series = []
    real_pnl_series = []
    fill_diff_series = []
    real_vega_series = []
    q_series = []

    prices = {
        80: [[], []],
        90: [[], []],
        100: [[], []],
        110: [[], []],
        120: [[], []]
    }

    orders = {
        80: [[], []],
        90: [[], []],
        100: [[], []],
        110: [[], []],
        120: [[], []]
    }

    fill_count = 0

    for line in output_file.readlines():
        if line[:6] == "Vol = ":
            vol = float(line[6:])
            estimate_vol_series.append(vol)
        elif line[:11] == "Real Vol = ":
            real_vol = float(line[11:])
            true_vol_series.append(real_vol)
        elif line[:6] == "PnL = ":
            pnl = float(line[6:])
            pnl_series.append(pnl)
        elif line[:12] == "Real vega = ":
            real_vega = float(line[12:])
            real_vega_series.append(real_vega)
        elif line[:11] == "Real PnL = ":
            pnl = float(line[11:])
            real_pnl_series.append(pnl)
        elif line[:12] == "Fill diff = ":
            fill_diff = float(line[12:])
            fill_diff_series.append(fill_diff)
        elif line[:7] == "Quote: ":
            l = map(float, line[7:-1].split("|"))
            prices[int(l[0])][0].append(l[1])
            prices[int(l[0])][1].append(l[2])
        elif line[:7] == "Order: ":
            strike, price, dir, tick = map(float, line[7:-1].split("|"))
            d = 1 if int(dir) == 1 else 0
            orders[int(strike)][d].append((tick, price))
        elif line[:4] == "q = ":
            q_series.append(float(line[4:]))
        elif line[:10] == "Quote Fill":
            fill_count += 1


    vol_diff = np.subtract(true_vol_series, estimate_vol_series)
    vol_residual = npla.norm(vol_diff)

    output_file.close()
    vol_file.close()

    if show_plot:
        n = 9 if PLOT_PRICE else 4
        fig, axes = plt.subplots(nrows=n)
        #ax = fig.add_subplot(2, 1, 1)

        L = len(true_vol_series)

        h1, = axes[0].plot(np.arange(0, L), true_vol_series)
        h2, = axes[0].plot(np.arange(0, L), estimate_vol_series)
        h3, = axes[1].plot(np.arange(0, L), real_pnl_series)
        h4, = axes[1].plot(np.arange(0, L), pnl_series)
        h5, = axes[2].plot(np.arange(0, L), real_vega_series)
        h7, = axes[3].plot(np.arange(0, L), fill_diff_series)
        #h8, = axes[4].plot(q_series)

        if PLOT_PRICE:
            for i in xrange(0, 5):
                axes[4+i].plot(prices[80 + 10*i][0])
                axes[4+i].plot(prices[80 + 10*i][1])
                axes[4+i].scatter(*zip(*orders[80 + 10*i][0]), color='blue')
                axes[4+i].scatter(*zip(*orders[80 + 10*i][1]), color='red')
                axes[4+i].set_xlim([0, 100])

        #axes[0].legend([h1, h2], ['true', 'guess'], loc=1)
        #axes[1].legend([h3, h4], ['real pnl', 'pnl'], loc=2)
        #axes[2].legend([h5], ['vega'], loc=2)

        print str(fill_count) + " fills"
        print str(vol_residual) + " - vol residual"
        print str(real_pnl_series[-1]) + " - PnL"

        plt.show()

    return real_pnl_series[-1], vol_residual, fill_count

if __name__ == "__main__":
    analyze(show_plot=True)