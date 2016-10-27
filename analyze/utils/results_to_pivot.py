#!/usr/bin/env python

import os
import sys

import pandas as pd
import numpy as np

from util import get_all_zero_events

def usage(progname):
    print('usage:', progname, '[data_input_dir]', file=sys.stderr)
    sys.exit(0)

def result_to_matrix(df):
    """
    Transform the result as read from results.csv in a matrix of the following format:

    EVENT1  EVENT2  EVENT3 .... EVENTN
    12           9       5          12
     1           1       2           5
     0         NaN     100          12
     0         NaN     NaN          99

    Note: NaN numbers may appear for an event at the end in case the individual events
    can be read from different runs containing a different amount of samples.
    Differences of just a few samples is normally not a problem. Big discrepancies
    would indicate unstable runtimes of your algorithm.
    """
    frames = []
    for idx in df.index.unique():
        series = df.loc[[idx], 'SAMPLE_VALUE']
        new_series = series.rename(idx).reset_index(drop=True)
        frames.append(new_series)

    # Column i is event i
    return pd.concat(frames, axis=1)

def minimum_nan_index(df):
    """
    Return the earliest index that contains NaN over all columns or None
    if there are no NaN values in any columns.

    # Example
    For the following matrix it returns 1 as (1,1) is NaN:
    idx | EVENT1   EVENT2  EVENT3 .... EVENTN
      0 |     12        9       5          12
      1 |      1      NaN       2           5
      2 |      0      NaN     100          12
      3 |      0      NaN       1          99
    """
    print(df.isnull().any(axis=1))
    for idx, has_null in df.isnull().any(axis=1).items():
        if has_null:
            return idx

def get_results_file(data_input):
    """
    Path to results.csv file, as generated by `autoperf extract`.
    """
    data_file = os.path.join(data_input, 'result.csv')
    return data_file

def persist_correlation(correlation_file, events, correlation_matrix):
    "Writes the correlation matrix (pairwise correlation value for every event) to file."
    with open(correlation_file, 'w') as f:
        header = '\t{}\n'.format('\t'.join([str(i) for i in events]))
        f.write(header)
        for i in events:
            f.write('{}'.format(i))
            for j in events:
                f.write('\t{}'.format(correlation_matrix.ix[i, j]))
            f.write('\n')

def persist_correlated_events(correlated_events_file, events, event_names, correlation_matrix):
    with open(correlated_events_file, 'w') as f:
        degree_to_events_dict = {}
        # Find correlated events for each event
        for i in events:
            correlated_events = [
                j for j in events
                if i != j and correlation_matrix.ix[i, j] >= CORRELATION_CUTOFF
            ]
            n = len(correlated_events)
            if n not in degree_to_events_dict:
                degree_to_events_dict[n] = []
            degree_to_events_dict[n].append(i)

            f.write('Event {} {} ({})\n'.format(i, event_names[i],
                                                len(correlated_events)))
            for j in correlated_events:
                f.write('\t{:3d} {:.2f} {}\n'.format(
                    j, correlation_matrix.ix[i, j], event_names[j])
                )
        f.write('-' * 50 + '\n')
        for n in sorted(degree_to_events_dict, reverse=True):
            l = degree_to_events_dict[n]
            f.write('{} ({}): {}\n'.format(n, len(l),
                                           ', '.join([str(i) for i in l])))

def persist_excluded_events(excluded_events_file, excluded_events):
    with open(excluded_events_file, 'w') as f:
        # Find correlated events for each event
        for i in excluded_events:
            f.write('{}\n'.format(i))

def get_benchmark_data_files(benchmark, plot_output_dir):
    verify_scheme(benchmark)
    data_files = []
    for process_idx, process in enumerate(benchmark.processes):
        process_name = get_process_name(benchmark, process_idx)
        data_file = get_results_file(plot_output_dir, benchmark, process_idx)
        data_files.append((process_name, data_file))
    return data_files

def time_to_ms(df):
    df['TIME'] = df['TIME'].map(lambda x: int(x * 1000))

def main(argv):
    if len(argv) > 2:
        usage(argv[0])

    data_directory = argv[1]
    # Parsed results.csv:
    raw_data = pd.read_csv(get_results_file(data_directory), sep=',', skipinitialspace=True)
    raw_data.sortlevel(inplace=True)
    time_to_ms(raw_data)
    grouped_df = raw_data.groupby(['EVENT_NAME', 'TIME']).sum()
    grouped_df.reset_index(level=['TIME'], inplace=True)
    #print grouped_df
    #sys.exit(1)

    # Remove events whose deltas are all 0:
    #df = grouped_df.drop(get_all_zero_events(grouped_df))
    df = result_to_matrix(grouped_df)
    cut_off = minimum_nan_index(df)
    if cut_off != None:
        df = df[:cut_off]
        #print df

    df.to_csv(os.path.join(data_directory, "transformed.csv"))

if __name__ == '__main__':
    main(sys.argv)