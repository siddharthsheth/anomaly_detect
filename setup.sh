mkdir anomalydetect
cd anomalydetect

git clone https://www.github.com/siddharthsheth/metricspaces
git clone https://www.github.com/siddharthsheth/greedypermutation
git clone https://www.github.com/siddharthsheth/anomaly_detect

pip install -e metricspaces
pip install -e greedypermutation

pip install scikit-learn
pip install 'influxdb-client[ciso]'

python greedy_tree_anomaly_detector.py