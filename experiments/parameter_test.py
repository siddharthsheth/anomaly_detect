'''
This experiment performs hyper-parameter tuning on window_size and std_param.
'''

from os import chdir, getcwd
from csv import reader
from anomaly_detect.greedytreemodel import GreedyTreeModel, MetricSpace
from anomaly_detect.timeseriespoint import TimeSeriesPoint, Point

def load_boot_data():
    # output = []
    with open('experiments/new_boot_data.csv', 'r') as test:
        testreader = reader(test)
        next(testreader)
        # test_data = [(line[0], (float(line[1]), float(line[2])), int(line[4]), (float(line[5]), float(line[6])), int(line[8])) for line in testreader]
        return [(line[0], (float(line[-2]), float(line[-1]))) for line in testreader]

chdir(getcwd())

window_sizes = [1,2,3,5,7,9,10,15]
std_params = [1,2,3,4,5,6,7,8,9,10]
# window_sizes = [3]
# std_params = [2]
for window_size in window_sizes:
    print(f'Window size= {window_size}')
    model = GreedyTreeModel(window_size, load_boot_data())
    min_rad = min(model.radii)
    max_rad = max(model.radii)
    model.radii -= {min_rad, max_rad}
    test_data = []
    with open('experiments/new_test_data.csv', 'r') as test:
        testreader = reader(test)
        next(testreader)
        test_data = [(line[0], *[(((float(line[3*i+1]), float(line[3*i+2]))), int(line[3*i+3])) for i in range(5)], int(line[-1])) for line in testreader]
    test_len = len(test_data)

    raw_tests = [model.scaler.transform([test_data[i][j+1][0] for i in range(test_len)]) for j in range(5)]
    test_sols = [[test_data[i][j+1][1] for i in range(window_size, test_len)] for j in range(5)]
    tests = [MetricSpace(TimeSeriesPoint(Point(test[i-j]) for j in range(window_size)) for i in range(window_size, test_len)) for test in raw_tests]
    with open('experiments/output.txt', 'a') as output:
        for std_param in std_params:
            print(f'Std_param = {std_param}')
            
            test_preds = [[model.pred_point(point, std_param) for point in test] for test in tests]            
            output.write(f'std_param = {std_param}, window_size = {window_size}\n')
            for radius in sorted(model.radii):
                output.write(f'{radius}: Mean= {model.radii_thresholds[radius]["mean"]:0.2f},  Std Dev= {model.radii_thresholds[radius]["std"]:0.2f}, Range= {model.radii_thresholds[radius]["mean"] - std_param*model.radii_thresholds[radius]["std"]:0.2f} - {model.radii_thresholds[radius]["mean"] + std_param*model.radii_thresholds[radius]["std"]:0.2f} \n')
    
            for i in range(5):
                # print(f'Running test {i+1}.')
                fp, fn, tp, tn = 0, 0, 0, 0
                for j, p in enumerate(test_preds[i]):
                    if test_sols[i][j] != p[1]:
                        if p[1] == 1:
                            fp += 1
                        else:
                            fn += 1
                    else:
                        if p[1] == 1:
                            tp += 1
                        else:
                            tn += 1
                output.write(f'Test {i+1}: FP- {fp} FN- {fn} TP- {tp} TN- {tn} \n')
            output.write('-----------------------------------------\n')