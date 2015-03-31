import matplotlib.pyplot as plt
import numpy as np
import numpy.linalg as npla
import sys
from os import path

def make_training_data():

    training_fname = "training_file_{}.txt".format(sys.argv[1])

    output_file = open(path.join(path.dirname(path.dirname(__file__)), 'output.txt'), 'r')

    if not path.isfile(training_fname):
        training_file = open(training_fname, 'w')
    else:
        training_file = open(training_fname, 'a')

    vol_diff = ""
    vega_series = ""

    for line in output_file.readlines():
        if line[:11] == "Vol diff = ":
            vol_diff = line[11:-1]
        elif line[:14] == "vega series = ":
            vega_series = ",".join(line[14:-1].split("|"))

        if vol_diff != "" and vega_series != "":
            training_file.write("{}{}\n".format(vega_series, vol_diff))
            vol_diff = ""
            vega_series = ""


    training_file.close()
    output_file.close()

if __name__ == "__main__":
    make_training_data()