#!/usr/bin/env python

import os
import sys
import time
import argparse
import re
import subprocess

import pandas as pd
import numpy as np
from matplotlib import pyplot as plt, font_manager

from runtimes import get_runtime_dataframe, get_runtime_pivot_tables
from util import *

from sklearn import svm
from sklearn import metrics
from sklearn import preprocessing

from svm import get_training_and_test_set, get_svm_metrics
from svm_topk import get_selected_events

AUTOPERF_PATH = os.path.join(sys.path[0], "..", "..", "target", "release", "autoperf")

def mkgroup(cfs_ranking_file):
    ret = subprocess.check_output([AUTOPERF_PATH, "mkgroup", "--input", cfs_ranking_file])
    lines = ret.split(os.linesep)
    assert lines[-1] == ''
    return lines[:-1]

if __name__ == '__main__':
    pd.set_option('display.max_rows', 37)
    pd.set_option('display.max_columns', 15)
    pd.set_option('display.width', 200)

    parser = argparse.ArgumentParser(description='Get the SVM parameters when limiting the amount of features.')
    parser.add_argument('--data', dest='data_directory', type=str, help="Data directory root.")

    parser.add_argument('--cutoff', dest='cutoff', type=float, default=1.15, help="Cut-off for labelling the runs.")
    parser.add_argument('--uncore', dest='uncore', type=str, help="What uncore counters to include.",
                        default='shared', choices=['all', 'shared', 'exclusive', 'none'])
    parser.add_argument('--config', dest='config', nargs='+', type=str, help="Which configs to include (L3-SMT, L3-SMT-cores, ...).",
                        default=['L3-SMT', 'L3-SMT-cores'])
    parser.add_argument('--cfs', dest='cfs', type=str, help="Weka file containing reduced, relevant features.")
    parser.add_argument('--tests', dest='tests', nargs='+', type=str, help="Which programs to use as a test set.")
    args = parser.parse_args()


    if not args.tests:
        runtimes = get_runtime_dataframe(args.data_directory)
        tests = map(lambda x: [x], sorted(runtimes['A'].unique()))
    else:
        tests = [args.tests]

    results_table = pd.DataFrame()

    for test in tests:
        if not args.cfs:
            cfs_default_file = os.path.join(args.data_directory, "topk_svm_{}_{}.csv"
                .format('_'.join(test), '_'.join(args.config)))
            if not os.path.exists(cfs_default_file):
                print "Skipping {} because we didn't find the cfs file {}".format(' '.join(test), cfs_default_file)
                continue
            event_list = mkgroup(cfs_default_file)
        else:
            event_list = mkgroup(args.cfs)

        X_all, Y, X_test_all, Y_test = get_training_and_test_set(args, test)

        X = pd.DataFrame()
        X_test = pd.DataFrame()

        for event in event_list:
            X[event] = X_all[event]
            X_test[event] = X_test_all[event]

        clf = svm.SVC(kernel='linear')
        min_max_scaler = preprocessing.MinMaxScaler()
        X_scaled = min_max_scaler.fit_transform(X)
        X_test_scaled = min_max_scaler.transform(X_test)

        clf.fit(X_scaled, Y)
        Y_pred = clf.predict(X_test_scaled)

        row = get_svm_metrics(args, test, Y, Y_test, Y_pred)
        results_table = results_table.append(row, ignore_index=True)

    results_table.to_csv("svm_machine_aware.csv", index=False)
    results_table = results_table[['Test App', 'Samples', 'Error', 'Precision/Recall', 'F1 score']]
    print results_table.to_latex(index=False)