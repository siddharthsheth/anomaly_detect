from collections import Counter, defaultdict
from time import time
from greedypermutation.balltree import greedy_tree
from metricspaces import MetricSpace
from greedypermutation import Point
from anomaly_detect.timeseriespoint import TimeSeriesPoint
from sklearn.preprocessing import StandardScaler
import numpy as np
from operator import mul, truediv, gt, lt

class GreedyTreeModel():
    """
    This module represents a model to predict anomalies using the greedy tree.
    """
    def __init__(self, window_size, data=(), radii=()):
        self.window_size = window_size
        self.radii = radii if radii != () else set()
        if data != ():
            self.rebuild_model(data)
            
    def load_data(self, dataset):
        """
        Method to update self.data.
        Dataset should be a list of tuples of the type (timestamp, metrics).
        """
        self.timestamps, data = zip(*dataset)

        self.scaler = StandardScaler()
        data = self.scaler.fit_transform(data)

        self.data = [(self.timestamps[i], TimeSeriesPoint((Point(data[i-j]) for j in range(self.window_size)))) for i in range(self.window_size, len(data))]

    def build_tree(self):
        """
        Method to build greedy tree on self.data and store it as self.tree.
        """
        print(f'Training on {len(self.data)} data points.')
        mass = Counter([point for _, point in self.data])
        points, mass = zip(*mass.items())
        # print(f'total mass = {sum(mass)}')

        print('Starting greedy tree construction.')
        start = time()
        M = MetricSpace(points)
        # print(f'no of unique points: {len(M)}') 
        self.tree = greedy_tree(M, mass=mass)
        print(f'Tree construction time: {time()-start:.2f} s.')

    def build_model(self):
        """
        Method to build outlier detection model using self.data and self.tree.
        """
        if self.data is None:
            print('Data needs to be loaded before building model.')
            return
        if self.tree is None:
            print('Tree needs to be built before building model.')
            return
        
        print('Getting radii thresholds.')
        start = time()

        if self.radii == set():
            self.radii_thresholds = defaultdict(dict)
            self.get_radii()
        else:
            radii_freqs = {radius: np.array([self.tree.range_count(point, radius) for _, point in self.data]) for radius in self.radii}
            self.radii_thresholds = {radius: {'mean': np.mean(radii_freqs[radius]), 'std': np.std(radii_freqs[radius])} for radius in self.radii}

        for radius in sorted(self.radii):
            print(f'{radius}: Mean= {self.radii_thresholds[radius]["mean"]},  Std Dev= {self.radii_thresholds[radius]["std"]}')
        print(f'Preprocessing time: {time()-start:.2f} s')

    def pred_point(self, point, std_param=1):
        """
        Method to predict whether `point` is outlier or not.
        Returns a pair: the first element is a list of tuples of the form (r, count_r) for all r that were out of the threshold range, 
            and the second element is a prediction: 0 for normal, 1 for outlier.
        """
        counts = {radius: self.tree.range_count(point, radius) for radius in self.radii}
        return ([(radius, counts[radius]) for radius in self.radii 
                        if (counts[radius] < self.radii_thresholds[radius]['mean'] - std_param*self.radii_thresholds[radius]['std'] -1 or
                            counts[radius] > self.radii_thresholds[radius]['mean'] + std_param*self.radii_thresholds[radius]['std'])
                ],
                0 if all(counts[radius] >= self.radii_thresholds[radius]['mean'] - std_param*self.radii_thresholds[radius]['std'] -1 and
                            counts[radius] <= self.radii_thresholds[radius]['mean'] + std_param*self.radii_thresholds[radius]['std'] 
                            for radius in self.radii
                        ) else 1)

    def rebuild_model(self, data):
        """
        Method to rebuild model using fresh data.
        """
        self.load_data(data)
        self.build_tree()
        self.build_model()

    def get_radii(self):
        """
        Method to get minimum number of radii of the form 2^i such that balls of the smallest radius centered at every point in self.data contain only 1 point and
            balls of the largest radius cover all points in self.data.
        """
        # store all radii
        counts = defaultdict(dict)
        radius_limits = defaultdict(dict)
        for _, point in self.data:
            # get upper bound radius
            counts[point] = self.get_counts_at_scales(point, 1, False)
            radius_limits[point]['max_rad'] = max(counts[point].keys())
            
            # get lower bound radius
            counts[point] = {**counts[point], **self.get_counts_at_scales(point, 0.5, True)}
            radius_limits[point]['min_rad'] = min(counts[point].keys())

            # tightening the bounds
            radius = radius_limits[point]['max_rad']
            while counts[point][radius/2] == len(self.data):                # Case: radius=1 is too big
                del counts[point][radius]
                radius_limits[point]['max_rad'] = radius/2
                radius /= 2

            radius = radius_limits[point]['min_rad']
            while counts[point][2*radius] == 1:                             # Case: radius=1 is too small
                del counts[point][radius]
                radius_limits[point]['min_rad'] = radius*2
                radius *= 2
        
            self.radii = self.radii.union(set(counts[point].keys()))        # update self.radii

        # compute radius thresholds
        for radius in self.radii:
            rad_counts = []
            for _, point in self.data:
                if radius in counts[point]:
                    rad_counts.append(counts[point][radius])
                elif radius > radius_limits[point]['max_rad']:
                    rad_counts.append(len(self.data))
                else:
                    rad_counts.append(1)
            self.radii_thresholds[radius] = {'mean': np.mean(rad_counts), 'std': np.std(rad_counts)}
    
    def get_counts_at_scales(self, point, start, halve):
        """
        Helper method for get_radii().
        """
        counts = dict()
        radius = start
        count = self.tree.range_count(point, radius)
        if halve is True:
            scale = truediv
            benchmark = 1
            comparator = gt
        else:
            scale = mul
            benchmark = len(self.data)
            comparator = lt
        
        while comparator(count, benchmark):
            counts[radius] = count
            radius = scale(radius, 2)
            count = self.tree.range_count(point, radius)

        counts[radius] = benchmark
        return counts