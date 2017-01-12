import os, sys

from matplotlib import pyplot as plt, font_manager
import numpy as np
import pandas as pd

import matplotlib
matplotlib.rc('pdf', fonttype=42)
plt.style.use([os.path.join(sys.path[0], '..', 'ethplot.mplstyle')])

ticks_font = font_manager.FontProperties(family='Decima Mono')
plt.style.use([os.path.join(sys.path[0], '../ethplot.mplstyle')])
NAME = "counters_vs_events"

if __name__ == '__main__':
    fig = plt.figure()

    raw_data = pd.read_csv(os.path.join(sys.argv[1], "events.csv"), skipinitialspace=True)
    raw_data['year'].map(lambda y: int(y))
    raw_data.sort_values(by=['year', 'counters'], inplace=True)
    raw_data.set_index('year', inplace=True)
    raw_data['events'] = raw_data['core events'] + raw_data['uncore events']

    ax1 = fig.add_subplot(1, 1, 1)

    ax1.set_ylabel('Hardware Performance Events')
    ax1.set_xlabel('Year of Release')

    ax1.spines['top'].set_visible(False)
    ax1.spines['right'].set_visible(False)
    ax1.get_xaxis().tick_bottom()
    ax1.get_yaxis().tick_left()
    ax1.set_xlim(2007.5, 2016.5)

    for row in raw_data.iterrows():
        year = row[0]
        name = row[1]['architecture']
        events = row[1]['events']

        xpos = year + 0.1
        ypos = events

        if year == 2016:
            xpos = 2014.7
        if name == "Westmere EP":
            ypos -= 20
        if name == "BroadwellX":
            ypos -= 70
            xpos += 0.1
        if name == "Broadwell":
            xpos -= 1.2
        if name == "KnightsLanding":
            ypos += 35
            xpos -= 0.3
        if name == "Goldmont":
            xpos += 0.2
        if name == "Skylake":
            ypos -= 55
        if name == "NehalemEP":
            xpos -= 1.2
            ypos += 35
        if name == "NehalemEX": # 553
            xpos -= 0.8
            ypos += 55
        if name == "WestmereEP-SP": # 576
            name = "WestmereEP"
            xpos -= 0.8
            ypos -= 110
        if name == "WestmereEP-DP": # 542
            continue # ignore this event (same as EP-SP..)

        ax1.annotate(name, xy=(xpos, ypos), xytext=(xpos, ypos), weight='light')

    p = ax1.plot(raw_data['events'], marker='o', linestyle='None')
    p = ax1.plot(raw_data['counters'])
    plt.xticks(raw_data.index.unique())

    ax1.annotate("HW Counters per Core", xy=(2014, 0), xytext=(2013.4, 29), color=p[0].get_color())

    ax1.get_xaxis().get_major_formatter().set_useOffset(False)
    plt.setp(ax1.get_xticklabels(), fontproperties=ticks_font)
    plt.setp(ax1.get_yticklabels(), fontproperties=ticks_font)


    plt.savefig(os.path.join(sys.argv[1], NAME + ".png"), format='png', pad_inches=0.0)
    plt.savefig(os.path.join(sys.argv[1], NAME + ".pdf"), format='pdf', pad_inches=0.0)
