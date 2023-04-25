mkdir anomaly_detect
cd anomaly_detect

git clone https://siddharthsheth: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@github.com/metricspaces
git clone https://siddharthsheth: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@github.com/greedypermutation

pip install -e metricspaces
pip install -e greedypermutation

pip install scikit-learn
pip install 'influxdb-client[ciso]'