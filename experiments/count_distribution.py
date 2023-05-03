'''
This experiment computes the frequency distribution of points at all radii for a particular window_size.
'''

from anomaly_detect.greedytreemodel import GreedyTreeModel
from anomaly_detect.timeseriespoint import TimeSeriesPoint, Point
from csv import reader
from matplotlib import pyplot as plt
import numpy as np

def load_boot_data():
    # output = []
    with open('experiments/new_boot_data.csv', 'r') as test:
        testreader = reader(test)
        next(testreader)
        # test_data = [(line[0], (float(line[1]), float(line[2])), int(line[4]), (float(line[5]), float(line[6])), int(line[8])) for line in testreader]
        return [(line[0], (float(line[-2]), float(line[-1]))) for line in testreader]
    
window_size = 1

model = GreedyTreeModel(window_size, load_boot_data())
_, data = zip(*load_boot_data())
data =model.scaler.transform(data)
test = [TimeSeriesPoint(Point(data[i-j]) for j in range(window_size)) for i in range(window_size, len(data))]
std_param = 6
for radius in sorted(model.radii):
    counts = np.array([model.tree.range_count(point, radius) for point in test])
    # print(f'r={radius}, counts={counts}')
    fig, ax = plt.subplots()
    ax.hist(counts)
    ax.set_title(f'r={radius}')
    ax.set_ylabel('Frequency')
    ax.set_xlabel('tree.range(p, r)')
    ax.set_ylim(0,220)
    ax.axvline(counts.mean()+6*counts.std(), color='k', linestyle='dashed', linewidth=1)
    ax.axvline(counts.mean()-6*counts.std(), color='k', linestyle='dashed', linewidth=1)
    ax.axvline(counts.mean()+3*counts.std(), color='gray', linestyle='dashed', linewidth=1)
    ax.axvline(counts.mean()-3*counts.std(), color='gray', linestyle='dashed', linewidth=1)
    plt.savefig(f'window_{window_size}_r_{radius}.png')

plt.show()