from influxdb_client import InfluxDBClient
from collections import defaultdict
import time

my_url = 'http://152.7.179.7:8086/'
my_org = 'f87217d97d859651'
my_uname = 'admin'
my_passwd = 'password'

client = InfluxDBClient(url=my_url, org=my_org, username=my_uname, password=my_passwd)
bucket = 'TrainingData'
tag = '_measurement'
tag_val = 'metrics'

def get_tree_boot_data():
    boot_start = 1682085600
    boot_stop = 1682091480
    # 2023-04-21T10:54:00Z
    # 2023-04-21T11:38:00Z

    data = get_tree_rebuild_data(boot_start, boot_stop)
    return [(entry, (data[entry]['cpuUsage'], data[entry]['memUsage'])) for entry in sorted(data)]

def get_tree_rebuild_data(start, stop: None):
    if stop == None:
        stop = 'now()'
    tables = client.query_api().query(f'from(bucket:"{bucket}") |> range(start: {start}, stop: {stop}) \
                                                                |> filter(fn: (r) => r.{tag} == "{tag_val}" and r.type == "container") \
                                                                |> truncateTimeColumn(unit: 1s) \
                                                                |> group(columns: ["_time", "_field"]) \
                                                                |> mean() \
                                                                |> sort(columns: ["_time"])')
    return convert_tables_to_dict(tables)

def get_active_containers(start: None):
    if start is None:
        start = '-2m'
    containers = set()
    tables = client.query_api().query(f'from(bucket:"{bucket}") |> range(start: {start}) \
                                                                |> filter(fn: (r) => r.{tag} == "{tag_val}" and r.type == "container" and r._field == "cpuUsage")')

    for table in tables:
        for row in table:
            containers.add(row['id'])
    
    return containers
    # with open('container_list.txt', 'r') as file:
    #     container_ids = [line[:-1] for line in file]

    # print(container_ids)

def get_new_data(start, container):
    tables = client.query_api().query(f'from(bucket:"{bucket}") |> range(start: {start}) \
                                                                |> filter(fn: (r) => r.{tag} == "{tag_val}" and r.id == "{container}") \
                                                                |> truncateTimeColumn(unit: 1s)')

    data = convert_tables_to_dict(tables)
    return [(entry, (data[entry]['cpuUsage'], data[entry]['memUsage'])) for entry in sorted(data)]

def convert_tables_to_dict(tables):
    data = defaultdict(dict)
    for table in tables:
        for row in table:
            data[row['_time']][row['_field']] = row['_value']
    return data

if __name__ == '__main__':
    pass