from collections import Counter
from time import time
from greedypermutation.balltree import greedy_tree
from metricspaces import MetricSpace
from greedypermutation import Point
from timeSeriesPoint import TimeSeriesPoint
from sklearn.preprocessing import StandardScaler
import numpy as np
from csv import reader
import influx

class GreedyTreeModel():
    def __init__(self, window_size, radii, data=()):
        self.window_size = window_size
        self.radii = radii
        if data is not None:
            self.rebuild_model(data)
            
    def load_data(self, dataset):
        self.timestamps, data = zip(*dataset)

        self.scaler = StandardScaler()
        data = self.scaler.fit_transform(data)

        self.data = [(self.timestamps[i], TimeSeriesPoint((Point(data[i-j]) for j in range(self.window_size)))) for i in range(self.window_size, len(data))]

    def build_tree(self):
        print(f'training on {len(self.data)} data points')
        mass = Counter([point for _, point in self.data])
        points, mass = zip(*mass.items())
        print(f'total mass = {sum(mass)}')

        print('starting tree construction')
        start = time()
        M = MetricSpace(points)
        print(f'no of unique points: {len(M)}') 
        self.tree = greedy_tree(M, mass=mass)
        print(f'construction time: {time()-start:.2f} s')

    def build_model(self):
        if self.data is None:
            print('Data needs to be loaded before building model.')
        if self.tree is None:
            print('Tree needs to be built before building model.')
            return
        
        print('getting radii thresholds')
        start = time()

        radii_freqs = {radius: np.array([self.tree.range_count(point, radius) for _, point in self.data]) for radius in self.radii}
        self.radii_thresholds = {radius: {'mean': np.mean(radii_freqs[radius]), 'std': np.std(radii_freqs[radius])} for radius in self.radii}

        for radius in self.radii:
            print(f'{radius}: {self.radii_thresholds[radius]["mean"] - self.radii_thresholds[radius]["std"]} - {self.radii_thresholds[radius]["mean"] + self.radii_thresholds[radius]["std"]}')
        print(f'preprocessing time: {time()-start:.2f} s')

    def pred_point(self, point):
        counts = {radius: self.tree.range_count(point, radius) for radius in self.radii}
        return (tuple(counts.items()), 0 if any(counts[radius] > self.radii_thresholds[radius]['mean'] - self.radii_thresholds[radius]['std'] and counts[radius] < self.radii_thresholds[radius]['mean'] + self.radii_thresholds[radius]['std'] for radius in self.radii) else 1)

    def rebuild_model(self, data):
            self.load_data(data)
            self.build_tree()
            self.build_model()

class AnomalyDetector():
    def __init__(self, window_size, radii, rebuild_period, stop_time=np.inf):
        self.model = GreedyTreeModel(window_size, radii, influx.get_tree_boot_data())
        self.rebuild_period = rebuild_period
        self.stop_time = stop_time

    def start(self):
        self.start = time()

    def rebuild():
                    

# def pred_point(point, tree, radii, radii_thresholds):
#     counts = [tree.range_count(point, radius) for radius in radii]
#     return (tuple(counts), 0 if not all(counts[i] > radii_thresholds[radius][0] - radii_thresholds[radius][1] or counts[i] < radii_thresholds[radius][0] + radii_thresholds[radius][1] for i, radius in enumerate(radii)) else 1)
    
if __name__ == '__main__':
    window_size, radii = 1, (0.125, 0.25, 0.5, 1, 2, 4, 8, 16, 32, 64)
    model = GreedyTreeModel(window_size, radii, influx.get_tree_boot_data())

    test_data = []
    with open('work/code-projects/anomaly_detect/test_data.csv', 'r') as test:
        testreader = reader(test)
        test_data = [(line[0], (float(line[1]), float(line[2])), int(line[4]), (float(line[5]), float(line[6])), int(line[8])) for line in testreader]
    
    test_len = len(test_data)

    test_1 = model.scaler.transform([test_data[i][1] for i in range(test_len)])
    test_1 = MetricSpace([TimeSeriesPoint((Point(test_1[i-j]) for j in range(window_size))) for i in range(window_size, test_len)])
    test_1_sol = [test_data[i][2] for i in range(window_size, test_len)]

    test_1_pred = [model.pred_point(point) for point in test_1]
    
    # for p in test_1_pred:
    #     print(p)
    print("Test 1:")
    for i, pred in enumerate(test_1_pred):
        if test_1_sol[i] != pred[1]:
            print(f'Mismatch at {test_data[i][0]}: actual is {test_1_sol[i]} while predicted {pred[1]}. Counts = {pred[0]}')

    test_2 = model.scaler.transform([test_data[i][3] for i in range(test_len)])
    test_2 = MetricSpace([TimeSeriesPoint((Point(test_2[i-j]) for j in range(window_size))) for i in range(window_size, test_len)])
    test_2_sol = [test_data[i][4] for i in range(window_size, test_len)]

    test_2_pred = [model.pred_point(point) for point in test_2]
    # for test_point in test_2:
    #     counts = [model.tree.range_count(test_point, radius) for radius in radii]
    #     test_2_pred.append((tuple(counts), 0 if not all(counts[i] > model.radii_thresholds[radius][0] - model.radii_thresholds[radius][1] or counts[i] < model.radii_thresholds[radius][0] + model.radii_thresholds[radius][1] for i, radius in enumerate(radii)) else 1))

    print("Test 2:")
    for i, pred in enumerate(test_2_pred):
        if test_2_sol[i] != pred[1]:
            print(f'Mismatch at {i}: actual is {test_2_sol[i]} while predicted {pred[1]}. Counts = {pred[0]}')
