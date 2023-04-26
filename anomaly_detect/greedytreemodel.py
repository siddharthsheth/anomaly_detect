from collections import Counter
from time import time
from greedypermutation.balltree import greedy_tree
from metricspaces import MetricSpace
from greedypermutation import Point
from timeSeriesPoint import TimeSeriesPoint
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import DBSCAN
import numpy as np
from csv import reader
import influx
from os import chdir, getcwd

"""
This module represents a model to predict anomalies using the greedy tree.
"""

class GreedyTreeModel():
    """
    
    """
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

    def pred_point(self, point, std_param=1):
        counts = {radius: self.tree.range_count(point, radius) for radius in self.radii}
        return ([(radius, counts[radius]) for radius in self.radii if counts[radius] < self.radii_thresholds[radius]['mean'] - std_param*self.radii_thresholds[radius]['std'] -1 or counts[radius] > self.radii_thresholds[radius]['mean'] + std_param*self.radii_thresholds[radius]['std']], 0 if all(counts[radius] >= self.radii_thresholds[radius]['mean'] - std_param*self.radii_thresholds[radius]['std'] -1 and counts[radius] <= self.radii_thresholds[radius]['mean'] + std_param*self.radii_thresholds[radius]['std'] for radius in self.radii) else 1)

    def rebuild_model(self, data):
        self.load_data(data)
        self.build_tree()
        self.build_model()

# def pred_point(point, tree, radii, radii_thresholds):
#     counts = [tree.range_count(point, radius) for radius in radii]
#     return (tuple(counts), 0 if not all(counts[i] > radii_thresholds[radius][0] - radii_thresholds[radius][1] or counts[i] < radii_thresholds[radius][0] + radii_thresholds[radius][1] for i, radius in enumerate(radii)) else 1)
    
if __name__ == '__main__':
    window_size, radii = 3, (0.125, 0.25, 0.5, 1, 2, 4, 8)
    # (1, 2, 4, 8, 16, 32, 64)
    # (0.03125/4, 0.03125/2, 0.03125, 0.0625, 0.125, 0.25, 0.5, 1, 2, 4, 8)
    model = GreedyTreeModel(window_size, radii, influx.get_tree_boot_data())



    test_data = []
    chdir(getcwd())
    with open('new_test_data.csv', 'r') as test:
        testreader = reader(test)
        next(testreader)
        # test_data = [(line[0], (float(line[1]), float(line[2])), int(line[4]), (float(line[5]), float(line[6])), int(line[8])) for line in testreader]
        test_data = [(line[0], *[(((float(line[3*i+1]), float(line[3*i+2]))), int(line[3*i+3])) for i in range(5)], int(line[-1])) for line in testreader]
    
    test_len = len(test_data)

    raw_tests = [model.scaler.transform([test_data[i][j+1][0] for i in range(test_len)]) for j in range(5)]
    test_sols = [[test_data[i][j+1][1] for i in range(window_size, test_len)] for j in range(5)]
    tests = [MetricSpace(TimeSeriesPoint(Point(test[i-j]) for j in range(window_size)) for i in range(window_size, test_len)) for test in raw_tests]
    test_preds = [[model.pred_point(point, 6) for point in test] for test in tests]

    db_preds = []
    dbscan = DBSCAN(eps=10, min_samples=3)
    for test in raw_tests:
        db_preds.append(dbscan.fit(test))
    for db_pred in db_preds:
        labels = db_pred.labels_

        # Number of clusters in labels, ignoring noise if present.
        n_clusters_ = len(set(labels)) - (1 if -1 in labels else 0)
        n_noise_ = list(labels).count(-1)

        print("Estimated number of clusters: %d" % n_clusters_)
        print("Estimated number of noise points: %d" % n_noise_)
    
    # for j in range(100):
    #     print(j+2, test_sols[1][j], test_preds[1][j])
    for i in range(5):
        # print(f'Running test {i+1}.')
        fp, fn = 0, 0
        for j, p in enumerate(test_preds[i]):
            if test_sols[i][j] != p[1]:
                if p[1] == 1:
                    fp += 1
                else:
                    fn += 1
                print(f'{j}- Mismatch at {test_data[j][0]}: actual is {test_sols[i][j]} while predicted {p[1]}. Point = {test_data[j][i+1][0]} Counts = {p[0]}')
        print(f'Test {i+1}: FP- {fp} FN- {fn}')