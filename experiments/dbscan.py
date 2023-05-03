'''
This experiment uses DBSCAN for benchmark comparison.
'''

from os import chdir, getcwd
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import DBSCAN
import numpy as np
from csv import reader

def load_boot_data():
    # output = []
    with open('experiments/new_boot_data.csv', 'r') as test:
        testreader = reader(test)
        next(testreader)
        # test_data = [(line[0], (float(line[1]), float(line[2])), int(line[4]), (float(line[5]), float(line[6])), int(line[8])) for line in testreader]
        return [(line[0], (float(line[-2]), float(line[-1]))) for line in testreader]

chdir(getcwd())
_, data = zip(*load_boot_data())
scaler = StandardScaler()
scaler.fit(data)
with open('experiments/new_test_data.csv', 'r') as test:
    testreader = reader(test)
    next(testreader)
    # test_data = [(line[0], (float(line[1]), float(line[2])), int(line[4]), (float(line[5]), float(line[6])), int(line[8])) for line in testreader]
    test_data = [(line[0], *[(((float(line[3*i+1]), float(line[3*i+2]))), int(line[3*i+3])) for i in range(5)], int(line[-1])) for line in testreader]

test_len = len(test_data)
raw_tests = [scaler.transform([test_data[i][j+1][0] for i in range(test_len)]) for j in range(5)]
test_sols = [[test_data[i][j+1][1] for i in range(test_len)] for j in range(5)]

db_preds = []
dbscan = DBSCAN(eps=1, min_samples=4)
for test in raw_tests:
    db_preds.append(dbscan.fit(test))
for j, db_pred in enumerate(db_preds):
    labels = db_pred.labels_
    fp, fn, tp, tn = 0, 0, 0, 0
    for i in range(len(labels)):
        label = 1 if labels[i] == -1 else 0
        if test_sols[j][i] != label:
            if label == 1:
                fp += 1
            else:
                fn += 1
        else:
            if label == 1:
                tp += 1
            else:
                tn += 1
            # print((f'Mismatch at {test_data[j][0]}: actual is {test_sols[i][j]} while predicted {p[1]}. Point = {test_data[j][i+1][0]} Counts = {p[0]}\n'))
    # Number of clusters in labels, ignoring noise if present.
    n_clusters_ = len(set(labels)) - (1 if -1 in labels else 0)
    n_noise_ = list(labels).count(-1)
    print(f'Test {j+1}-  FP: {fp}, FN: {fn}, TP: {tp}, TN: {tn}')
    print("Estimated number of clusters: %d" % n_clusters_)
    print("Estimated number of noise points: %d" % n_noise_)