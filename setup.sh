mkdir anomaly_detect
cd anomaly_detect

git clone https://siddharthsheth@github.com/metricspaces
git clone https://siddharthsheth@github.com/greedypermutation
# git clone https://siddharthsheth@github.com/anomaly_detect

pip install -e metricspaces
pip install -e greedypermutation

pip install scikit-learn
pip install 'influxdb-client[ciso]'

python greedy_tree_anomaly_detector.py