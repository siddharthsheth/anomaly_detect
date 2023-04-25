import influx
from model import GreedyTreeModel
from time import time, sleep
from collections import defaultdict
from timeSeriesPoint import TimeSeriesPoint
from greedypermutation import Point

period = '15s'

window_size, radii = 1, (0.125, 0.25, 0.5, 1, 2, 4, 8, 16, 32, 64)

model = GreedyTreeModel(window_size, radii, influx.get_tree_boot_data())
# timestamps, data, scaler = model.load_data()
# tree, radii_thresholds = model.build_model((timestamps, data), radii, window_size)

start = time()
temp_storage = defaultdict(list)
container_state = dict()

while time() - start < 600:
    containers = influx.get_active_containers(f'-{period}')

    for container in containers:
        data = influx.get_new_data(f'-{period}', container)
        print(container, data)
        for entry in data:
            scaled_entry = model.scaler.transform([entry[1]])[0]
            if len(temp_storage[container]) == window_size-1 or container in container_state:
                if len(temp_storage[container]) == window_size-1:
                    container_state[container] = {'point': TimeSeriesPoint((*temp_storage[container], Point(scaled_entry))), 'timestamp':entry[0]}
                    del temp_storage[container]
                elif entry[0] > container_state[container]['timestamp']:
                    container_state[container]['point'].slide_window(scaled_entry)
                    container_state[container]['timestamp'] = entry[0]
                print('About to predict')
                counters, pred = model.pred_point(container_state[container]['point'])
                if pred == 1:
                    print(f'Anomaly at {entry[0]} in container {container}: {counters}')
            else:
                temp_storage[container].append(Point(scaled_entry))
        
    sleep(15)
