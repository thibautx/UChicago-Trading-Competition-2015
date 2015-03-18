import matplotlib.pyplot as plt
import numpy as np
import numpy.linalg as npla


def analyze(show_plot=True):
    output_file = open('output.txt')
    vol_file = open('vol_data.txt')

    true_vol_series = [float(v) for v in vol_file.readlines()]

    estimate_vol_series = []
    pnl_series = []
    vega_series = []
    real_pnl_series = []
    fill_diff_series = []
    real_vega_series = []

    fill_count = 0

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
        elif line[:12] == "Real vega = ":
            real_vega = float(line[12:])
            real_vega_series.append(real_vega)
        elif line[:11] == "Real PnL = ":
            pnl = float(line[11:])
            real_pnl_series.append(pnl)
        elif line[:12] == "Fill diff = ":
            fill_diff = float(line[12:])
            fill_diff_series.append(fill_diff)
        else:
            fill_count += 1


    vol_diff = np.subtract(vol, estimate_vol_series)
    vol_residual = npla.norm(vol_diff)

    output_file.close()
    vol_file.close()

    if show_plot:
        fig, axes = plt.subplots(nrows=4)
        #ax = fig.add_subplot(2, 1, 1)

        L = len(true_vol_series)

        h1, = axes[0].plot(np.arange(0, L), true_vol_series)
        h2, = axes[0].plot(np.arange(0, L), estimate_vol_series)
        h3, = axes[1].plot(np.arange(0, L), real_pnl_series)
        h4, = axes[1].plot(np.arange(0, L), pnl_series)
        h5, = axes[2].plot(np.arange(0, L), real_vega_series)
        h6, = axes[2].plot(np.arange(0, L), vega_series)
        h7, = axes[3].plot(np.arange(0, L), fill_diff_series)

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