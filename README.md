# anomaly_detect
Anomaly detection in a distributed system using the greedy tree.

## Setup

Requires Python version 3.8.

```bash
mkdir anomalydetect
cd anomalydetect

git clone https://www.github.com/siddharthsheth/metricspaces
git clone https://www.github.com/siddharthsheth/greedypermutation
git clone https://www.github.com/siddharthsheth/anomaly_detect

pip install -e metricspaces
pip install -e greedypermutation
pip install -e anomaly_detect

pip install scikit-learn
pip install 'influxdb-client[ciso]'
```

## About

`anomaly_detect` is the main library.
Experiments from the paper can be reproduced by running the files in `experiments`.

To run the anomaly detector on a live distributed system, run
```python
python anomaly_detect/anomalydetector.py
```
However, this will only work if the system is running.
