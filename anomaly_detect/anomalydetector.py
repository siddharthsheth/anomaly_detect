from greedytreemodel import GreedyTreeModel
import influx
from time import time, sleep
from collections import defaultdict
from timeSeriesPoint import TimeSeriesPoint
from greedypermutation import Point
from numpy import inf
from requests import post

class AnomalyDetector():
    def __init__(self, radii, std_param=2, rebuild_period=1, cooldown=15, stop_time=inf, slo=3):
        self.model = GreedyTreeModel(slo, radii, influx.get_tree_boot_data())
        self.rebuild_period = rebuild_period*3600                                       # The greedy tree is rebuilt after this period (in hours)
        self.cooldown = cooldown                                                        # The detector waits for this period (in seconds) to fetch new data
        self.stop_time = stop_time
        self.temp_storage = defaultdict(list)
        self.containers = dict()
        self.potential_anomalies = defaultdict(int)
        self.slo = slo
        self.std_param = std_param

    def start(self):
        """
        Starts the anomaly detector.
        Rebuilds the greedy tree whenever the current one gets stale.
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
        potentially_anomalous_containers = set()
        for container in containers:
            # potentially_anomalous_containers = set()
            # last_pred_time = f'-{self.cooldown}s' if container not in self.containers else f'{self.containers[container]["timestamp"]}'
            last_pred_time = f'-{self.cooldown}s'
            if last_pred_time != f'-{self.cooldown}s':
                print(last_pred_time)
            data = influx.get_new_data(last_pred_time, container)
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
        if len(potentially_anomalous_containers) == len(containers):
            print('Clearing potential anomalies. Anomalous load in all containers detected.')
            self.potential_anomalies = defaultdict(int)
        else:
            self.update_potential_anomalies(potentially_anomalous_containers)
            
        sleep(self.cooldown)
    
    def update_potential_anomalies(self, potentially_anomalous_containers):
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
                # potentially_anomalous_containers.remove(container)
                x = post('http://152.7.179.7:8000/admin/containerrestart', json = {'container_id': container})
                # print(x)
        for container in to_delete:
            del self.potential_anomalies[container]

    def update_detector_state(self, scaled_entry, container, timestamp):
        """
        
        """
        if len(self.temp_storage[container]) == self.model.window_size-1:
            self.containers[container] = {'point': TimeSeriesPoint((*self.temp_storage[container], Point(scaled_entry))), 'timestamp': timestamp}
            del self.temp_storage[container]
        elif timestamp > self.containers[container]['timestamp']:
            self.containers[container]['point'].slide_window(scaled_entry)
            self.containers[container]['timestamp'] = timestamp

if __name__ == '__main__':
    slo, radii = 3, (0.25, 0.5, 1, 2, 4, 8)
    detector = AnomalyDetector(radii, slo=slo, std_param=6)
    detector.start()

    # containers = get('http://152.7.176.37:8000/container/list').text
    # containers = [container.strip('[]"\n') for container in containers.split(',')]
    # x = post('http://152.7.179.7:8000/admin/containerrestart', json={'container_id': containers[0]})
    # print(x)