import os
import subprocess
from options_vol_analysis import analyze
import numpy as np
import matplotlib.pyplot as plt
import itertools

from pprint import PrettyPrinter

PLOT = False

total_runs = 25

alpha = [1.3]
xi = [1.0]
ema_decay = [0.1]
edge_estimate = [0.03, 0.04, 0.05, 0.06, 0.07]
beta = [0.0, 0.1]
beta_decay = [0.4, 0.9]
hit_weight = [3]
miss_streak_weight = [5, 7]
miss_count_trigger = [3]


results = {}

params_hypercube = itertools.product(*[alpha, xi, ema_decay, edge_estimate, beta, beta_decay, hit_weight, miss_streak_weight, miss_count_trigger])

#print len([p for p in params_hypercube])

for params in params_hypercube:
    print params
    fill_series = []
    vol_res_series = []
    pnl_series = []

    for _ in xrange(0, total_runs):

        p = subprocess.Popen('C:\Python27\python.exe "C:/Users/Greg Pastorek/Documents/FEC/uchicago-algo/optionsCase/python/options_sim.py')

        p.wait()

        cmd = '"C:\\Program Files\\Java\\jdk1.8.0_25\\bin\\java" -Didea.launcher.port=7537 ' + \
              '-classpath "C:\\Program Files\\Java\jdk1.8.0_25\\jre\\lib\\charsets.jar;C:\\Program Files\\Java\\jdk1.8.0_25\\jre\\lib\\deploy.jar;' + \
              'C:\\Program Files\\Java\\jdk1.8.0_25\\jre\\lib\\javaws.jar;C:\\Program Files\\Java\\jdk1.8.0_25\\jre\\lib\\jce.jar;C:\\Program Files\\Java\\jdk1.8.0_25\\jre\\lib\\jfr.jar;' +\
              'C:\\Program Files\\Java\\jdk1.8.0_25\\jre\\lib\\jfxswt.jar;C:\\Program Files\\Java\\jdk1.8.0_25\\jre\\lib\\jsse.jar;' + \
              'C:\\Program Files\\Java\\jdk1.8.0_25\\jre\\lib\\management-agent.jar;C:\\Program Files\\Java\\jdk1.8.0_25\\jre\\lib\\plugin.jar;' +\
              'C:\\Program Files\\Java\\jdk1.8.0_25\\jre\\lib\\resources.jar;C:\\Program Files\\Java\\jdk1.8.0_25\\jre\\lib\\rt.jar;' + \
              'C:\\Program Files\\Java\\jdk1.8.0_25\\jre\\lib\\ext\\access-bridge-64.jar;C:\\Program Files\\Java\\jdk1.8.0_25\\jre\\lib\\ext\\cldrdata.jar;' + \
              'C:\\Program Files\\Java\\jdk1.8.0_25\\jre\\lib\\ext\\dnsns.jar;C:\\Program Files\\Java\\jdk1.8.0_25\\jre\\lib\\ext\\jaccess.jar;' +\
              'C:\\Program Files\\Java\\jdk1.8.0_25\\jre\\lib\\ext\\jfxrt.jar;C:\\Program Files\\Java\\jdk1.8.0_25\\jre\\lib\\ext\\localedata.jar;' +\
              'C:\\Program Files\\Java\\jdk1.8.0_25\\jre\\lib\\ext\\nashorn.jar;C:\\Program Files\\Java\\jdk1.8.0_25\\jre\\lib\\ext\\sunec.jar;'+\
              'C:\\Program Files\\Java\\jdk1.8.0_25\\jre\\lib\\ext\\sunjce_provider.jar;C:\\Program Files\\Java\\jdk1.8.0_25\\jre\\lib\\ext\\sunmscapi.jar;'+\
              'C:\\Program Files\\Java\\jdk1.8.0_25\\jre\\lib\\ext\\sunpkcs11.jar;C:\\Program Files\\Java\\jdk1.8.0_25\\jre\\lib\\ext\\zipfs.jar;'+\
              'C:\\Users\\Greg Pastorek\\Documents\\FEC\\uchicago-algo\\optionsCase;C:\\Users\\Greg Pastorek\\Documents\\FEC\\uchicago-algo\\libs\\commons-math3-3.4.1.jar;'+\
              'C:\\Users\\Greg Pastorek\\Documents\\FEC\\uchicago-algo\\libs\\options.jar;C:\\Users\\Greg Pastorek\\Documents\\FEC\\uchicago-algo\\libs\\index.jar;'+\
              'C:\\Users\\Greg Pastorek\\Documents\\FEC\\uchicago-algo\\libs\\freeway-6.0.jar;C:\\Users\\Greg Pastorek\\Documents\\FEC\\uchicago-algo\\libs\\pairs.jar;'+\
              'C:\\Program Files (x86)\\JetBrains\\IntelliJ IDEA Community Edition 14.0.1\\lib\\idea_rt.jar" com.intellij.rt.execution.application.AppMain Main '+\
              " ".join(map(str, params))

        p = subprocess.Popen(cmd, shell=True, stdout=open('C:\\Users\\Greg Pastorek\\Documents\\FEC\\uchicago-algo\\optionsCase\\python\\output.txt', 'w'))

        p.wait()

        pnl, vol_residual, fill_count = analyze(show_plot=False)
        print str(fill_count) + " fills"
        print str(vol_residual) + " - vol residual"
        print str(pnl) + " - PnL"
        fill_series.append(fill_count)
        vol_res_series.append(vol_residual)
        pnl_series.append(pnl)

    avg_fills = np.average(fill_series)
    avg_vol_res = np.average(vol_res_series)
    std_vol_res = np.std(vol_res_series)
    avg_pnl = np.average(pnl_series)
    pnl_std = np.std(pnl_series)
    profitable_count = np.sum(map(lambda x: x > 0, pnl_series))

    results[params] = (avg_fills, avg_vol_res, std_vol_res, avg_pnl, pnl_std, (profitable_count / float(total_runs)))

    print "Average number of fills was {}".format(avg_fills)
    print "Vol residual average was {}".format(avg_vol_res)
    print "Vol residual STD was {}".format(std_vol_res)
    print "PnL average is {}".format(avg_pnl)
    print "PnL STD is {}".format(pnl_std)
    print "Number of positive PnL runs was {} out of {}".format(profitable_count, total_runs)

    if PLOT:
        fig = plt.figure()
        ax = fig.add_subplot(2, 1, 1)

        ax.scatter(vol_res_series, pnl_series)
        plt.xlabel('Vol Residual')
        plt.ylabel('PnL')

        plt.show()


pp = PrettyPrinter(indent=4)

print "\n---BEST PnL AVG---\n"
pp.pprint(reversed(sorted(results.items(), key=lambda k: k[1][3]))[:30])