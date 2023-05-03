from anomaly_detect.greedytreemodel import GreedyTreeModel
from anomaly_detect.timeseriespoint import TimeSeriesPoint
import influx
from collections import defaultdict
from greedypermutation import Point
from numpy import inf
from time import time, sleep
from requests import post


class AnomalyDetector():
    """
    This class represents an anomaly detector using GreedyTreeModel.
    """
    def __init__(self, std_param=2, rebuild_period=1, cooldown=15, stop_time=inf, slo=3):
        self.model = GreedyTreeModel(slo, data=influx.get_tree_boot_data())     # The model used for outlier detection.
        self.rebuild_period = rebuild_period*3600                               # The GreedyTreeModel is rebuilt after this period (in hours)
        self.cooldown = cooldown                                                # The AnomalyDetector waits for this period (in seconds) to fetch new data
        self.stop_time = stop_time                                              # The AnomalyDetector is shut down after this time (in seconds)
        self.temp_storage = defaultdict(list)                                   # Store measurements per container until you have enough measurements to form a TimeSeriesPoint for that container.
        self.containers = dict()                                                # Store the last TimeSeriesPoint and timestamp for each active container.
        self.potential_anomalies = defaultdict(int)                             # Store the number of successive outliers detected for each container.
        self.slo = slo                                                          # The number of successive outliers for anomaly detection. Also the number of measurements required per container to create a TimeSeriesPoint.
        self.std_param = std_param                                              # The parameter to be used for prediction.

    def start(self):
        """
        Starts the AnomalyDetector.
        Rebuilds the GreedyTreeModel whenever the current one gets stale.
        """
        self.start = time()
        lifespan = time()
        print(f'Tree will be rebuilt in {self.rebuild_period} s.')
        while time() - self.start < self.stop_time:
            if time() - lifespan > self.rebuild_period:
                print('Tree is stale. Rebuilding the tree.')
                self.model.rebuild_model(influx.get_tree_rebuild_data(f'-{self.rebuild_period}s'))
                lifespan = time()
            self.predict_new_data()

    def predict_new_data(self):
        """
        Predicts anomalies in the latest data.
        """
        # print('Predicting new data')
        containers = influx.get_active_containers_master()
        # print(f'Fetching data for {len(containers)} containers.')
        potentially_anomalous_containers = self.get_potentially_anomalous_containers(containers)
        if len(potentially_anomalous_containers) == len(containers):
            print('Clearing potential anomalies. Anomalous load in all containers detected.')
            self.potential_anomalies = defaultdict(int)
        else:
            self.update_potential_anomalies(potentially_anomalous_containers)
            
        sleep(self.cooldown)
    
    def get_potentially_anomalous_containers(self, containers):
        """
        Given a list of containers, return a set of those that could potentially be anomalous.
        """
        potentially_anomalous_containers = set()
        for container in containers:
            data = influx.get_new_data(f'-{self.cooldown}s', container)
            # print(f'{len(data)} new records for container {container} whose last timestamp was {"" if container not in self.containers else self.containers[container]["timestamp"]}')
            for entry in data:
                scaled_entry = self.model.scaler.transform([entry[1]])[0]
                if len(self.temp_storage[container]) == self.model.window_size-1 or container in self.containers:
                    self.update_detector_state(scaled_entry, container, entry[0])
                    _, pred = self.model.pred_point(self.containers[container]['point'], self.std_param)
                    if pred == 1:
                        print(f'Prediction for {container}: {pred}')
                        potentially_anomalous_containers.add(container)
                else:
                    self.temp_storage[container].append(Point(scaled_entry))
        return potentially_anomalous_containers

    def update_potential_anomalies(self, potentially_anomalous_containers):
        """
        Given a set of potentially anomalous containers, check which of them are actually anomalous.
        """
        for container in potentially_anomalous_containers:
            print(f'Container {container} is potentially anomalous.')
            self.potential_anomalies[container] += 1
        to_delete =set()
        for container in self.potential_anomalies:
            if container not in potentially_anomalous_containers:
                print(f'Container {container} is no longer potentially anomalous.')
                to_delete.add(container)
            elif self.potential_anomalies[container] >= self.slo:
                print(f'Anomaly in container {container}')
                x = post('http://152.7.179.7:8000/admin/containerrestart', json = {'container_id': container})
                # print(x)
        for container in to_delete:
            del self.potential_anomalies[container]

    def update_detector_state(self, measurement, container, timestamp):
        """
        Given a new measurement and a corresponding timestamp for a container, 
        """
        if len(self.temp_storage[container]) == self.model.window_size-1:
            self.containers[container] = {'point': TimeSeriesPoint((*self.temp_storage[container], Point(measurement))), 'timestamp': timestamp}
            del self.temp_storage[container]
        elif timestamp > self.containers[container]['timestamp']:
            self.containers[container]['point'].slide_window(measurement)
            self.containers[container]['timestamp'] = timestamp

if __name__ == '__main__':
    slo = 3
    detector = AnomalyDetector(slo=slo, std_param=6)
    detector.start()