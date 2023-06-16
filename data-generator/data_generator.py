from influxdb_client import InfluxDBClient, Point, WriteOptions
from influxdb_client.client.write_api import SYNCHRONOUS
import urllib3
import time
from reactivex.scheduler import ThreadPoolScheduler

import os
import random

def generate_random_value(min_value, max_value):
    return round(random.uniform(min_value, max_value), 4)



host = os.getenv("INFLUXDB_HOST", "localhost")
influx_user = os.getenv("INFLUXDB_ADMIN_USER", "admin")
influx_password = os.getenv("INFLUXDB_ADMIN_PASSWORD", "password")
influx_org = os.getenv("INFLUXDB_ORG", "myorg")
influx_bucket = os.getenv("INFLUXDB_BUCKET", "somebucket")

port = os.getenv("INFLUXDB_PORT", 8086)

print(host, influx_user, influx_password, port, influx_bucket)

url = f'http://{host}:{port}'

def start_gen():

    while True:
        client = InfluxDBClient(url=url, username=influx_user, password=influx_password, org=influx_org)
        if client.ping() == False:
            print("retrying")
            time.sleep(1)
            continue
        else:
            break


        

    # client.switch_database(database)
    print("ping")
    print(client.ping())
    bucket_api = client.buckets_api()
    bucket = bucket_api.find_bucket_by_name(influx_bucket)

    stime = time.time()
    if bucket == None:
        bucket_api.create_bucket(bucket_name=influx_bucket, org=influx_org)
        print("Bucket is created.")

        measurement = "o2_reading"
        start_timestamp = int(time.time() - 5*5000000)
        print("start_timestamp", start_timestamp)
        print("start_timestamp", start_timestamp * 5)
        # data_points = []
        # write_client = client.write_api(write_options=SYNCHRONOUS)
        options = WriteOptions(
            batch_size=200,
            flush_interval=1000,
            jitter_interval=0,
            retry_interval=5000,
            max_retries=5,
            max_retry_delay=30_000,
            exponential_base=2,
            write_scheduler=ThreadPoolScheduler(max_workers=8)
        )
        write_client = client.write_api(write_options=options)
        print("start writing")
        for x in range(5000000):
            t = (start_timestamp) + (x * 5)
            
            write_client.write(
                influx_bucket, influx_org, 
                Point("o2_reading")
                .tag("sensor_id", 1)
                .tag("data_type_of_sensor", "univariate")
                .tag("subsensor", "o2")
                .field("value", generate_random_value(209460.0, 219460.0))
                .field("units", "ppm")
                .time(int(t), "s")
            )
        
        write_client.flush()
        write_client.close()
        client.close()

        print("Data generation complete.")
    else:
        client.close()

        print("Data already present.")
    print("took", time.time() - stime)


    """
    with client.write_api(write_options=SYNCHRONOUS) as write_client:
        write_client.write("mybucket", "myorg", Point("o2_reading").tag("sensor_id", 1).tag("data_type_of_sensor", "univariate").tag("subsensor", "o2").field("value", 100000.0).field("units", "ppm"))

    query = 'from(bucket: "mybucket") \
        |> range(start: -10m)'
    table = client.query_api().query(org="myorg", query=query)
    """

    def get_buckets():
        client = get_client()
        return client.buckets_api().find_buckets()



    def get_client():
        client = InfluxDBClient(url=url, username=influx_user, password=influx_password, org=influx_org)
        return client

    def delete_bucket(name):
        client = get_client()
        bk = client.buckets_api()
        b = bk.find_bucket_by_name(name)
        return bk.delete_bucket(b)
    
if __name__ == "__main__":
    print("running??")
    time.sleep(1)
    start_gen()