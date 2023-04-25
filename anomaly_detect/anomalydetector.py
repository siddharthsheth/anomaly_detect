from greedytreemodel import GreedyTreeModel
import influx
from time import time, sleep
from collections import defaultdict
from timeSeriesPoint import TimeSeriesPoint
from greedypermutation import Point
from numpy import inf

class AnomalyDetector():
    def __init__(self, window_size, radii, rebuild_period=1, cooldown=15, stop_time=inf):
        self.model = GreedyTreeModel(window_size, radii, influx.get_tree_boot_data())
        self.rebuild_period = rebuild_period*3600
        self.cooldown = cooldown
        self.stop_time = stop_time
        self.temp_storage = defaultdict(list)
        self.containers = dict()

    def start(self):
        self.start = time()
        lifespan = time()
        while time() - self.start < self.stop_time:
            if lifespan - time() > self.rebuild_period:
                print('Tree is stale. Rebuilding the tree.')
                self.model.rebuild_model(influx.get_tree_rebuild_data(f'{self.rebuild_period}s'))
                lifespan = time()
            self.predict_new_data()

    def predict_new_data(self):
        containers = influx.get_active_containers(f'-{self.cooldown}s')
        for container in containers:
            data = influx.get_new_data(f'-{2*self.cooldown}', container)
            # print(container, data)
            for entry in data:
                scaled_entry = self.model.scaler.transform([entry[1]])[0]
                if len(self.temp_storage[container]) == self.model.window_size-1 or container in self.containers:
                    if len(self.temp_storage[container]) == self.model.window_size-1:
                        self.containers[container] = {'point': TimeSeriesPoint((*self.temp_storage[container], Point(scaled_entry))), 'timestamp':entry[0]}
                        del self.temp_storage[container]
                    elif entry[0] > self.containers[container]['timestamp']:
                        self.containers[container]['point'].slide_window(scaled_entry)
                        self.containers[container]['timestamp'] = entry[0]
                    counters, pred = self.model.pred_point(self.containers[container]['point'])
                    if pred == 1:
                        print(f'Anomaly at {entry[0]} in container {container}: {counters}')
                else:
                    self.temp_storage[container].append(Point(scaled_entry))
            
        sleep(self.cooldown)

if __name__ == '__main__':
    window_size, radii = 1, (0.125, 0.25, 0.5, 1, 2, 4, 8, 16, 32, 64)
    detector = AnomalyDetector(window_size, radii)
    detector.start()