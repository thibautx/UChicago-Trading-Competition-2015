import os
import subprocess
from options_vol_analysis import analyze
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties
import itertools

from pprint import PrettyPrinter

SIMULATIONS = 100

alpha = 1.0
xi = 2.0
ema_decay = 0.9
edge_estimate = 0.04
beta = 0.0
beta_decay = 0.9
hit_weight = 5
miss_streak_weight = 3
miss_count_trigger = 3
iota = 0.0
fucked_up_trigger = 100

params = [alpha, xi, ema_decay, edge_estimate, beta, beta_decay, hit_weight, miss_streak_weight, miss_count_trigger, iota, fucked_up_trigger]


for i in xrange(0, SIMULATIONS):

    print i

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

    p = subprocess.Popen('C:\Python27\python.exe "C:/Users/Greg Pastorek/Documents/FEC/uchicago-algo/optionsCase/python/Volatility Prediction ML/make_training.py" "{}"'.format("-".join(map(str, params))))

    p.wait()