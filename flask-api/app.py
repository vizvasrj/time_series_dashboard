from flask import Flask, jsonify, request, url_for
from flask_cors import CORS
from influxdb_client import InfluxDBClient
from influxdb_client.rest import ApiException
import os
import time

host = os.getenv("INFLUXDB_HOST", "localhost")
influx_user = os.getenv("INFLUXDB_ADMIN_USER", "admin")
influx_password = os.getenv("INFLUXDB_ADMIN_PASSWORD", "password")
influx_org = os.getenv("INFLUXDB_ORG", "myorg")
influx_bucket = os.getenv("INFLUXDB_BUCKET", "somebucket")

port = os.getenv("INFLUXDB_PORT", 8086)

print(host, influx_user, influx_password, port, influx_bucket)

url = f'http://{host}:{port}'

app = Flask(__name__)

CORS(app)

def get_client():
    client = InfluxDBClient(
        url=url, username=influx_user, 
        password=influx_password, 
        org=influx_org, timeout=300000
    )
    return client

global client
client = get_client()

@app.route("/")
def index():
    return "Index"

@app.route("/api/oxygen_data", methods=["GET"])
def get_oxygen_data():
    unit = request.args.get("unit")
    if unit is None:
        unit = 5
    else:
        unit = int(unit)
    
    dtype = request.args.get("dtype") # s, m, d
    if dtype is None or dtype not in ["ns", "us", "ms", "s", "m", "h", "d", "w", "mo", "y"]:
        dtype = "s"


    limit = request.args.get("limit")
    if limit is None:
        limit = 20
    else:
        try:
            limit = int(limit)
            if limit < 10 or limit > 100:
                limit = 20  # Use default limit if out of range
        except ValueError:
            limit = 20  # Use default limit if invalid value

        
    offset = request.args.get("offset")
    if offset is None:
        offset = 0
    else:
        try:
            offset = int(offset)
            if offset < 0:
                offset = 0  # Use default offset if negative
        except ValueError:
            offset = 0  # Use default offset if invalid value


    # need to check of these
    datas = get_every(unit, dtype, limit, offset)
    next_offset = offset + limit
    prev_offset = max(offset - limit, 0)
    base_url = request.base_url
    print(base_url)
    next_url = url_for("get_oxygen_data", unit=unit, limit=limit, offset=next_offset, dtype=dtype)
    print(next_url)
    if next_offset == limit:
        prev_url = None
        pass
    else:
        prev_url = url_for("get_oxygen_data", unit=unit, limit=limit, offset=prev_offset, dtype=dtype)

    # Return the data and URLs as a dictionary
    response = {
        "data": datas,
        "next_url": next_url,
        "prev_url": prev_url
    }
    # print("datas", datas)
    return response, 200

    


def get_every(
        unit:int=5, dtype:str="s", 
        limit:int=20, offset:int=0,
    )->dict:
    while True:
        global client
        print(unit, dtype, limit, offset)
        """
        this function is used to filter result based on many factors.
        - `unit` represents the interval unit (e.g., 5 for 5 minutes).
        - `dtype` represents the interval type ('s' for seconds, 'm' for minutes, 'd' for days).
                ns: nanosecond
                us: microsecond
                ms: millisecond
                s: second
                m: minute
                h: hour
                d: day
                w: week
                mo: calendar month
                y: calendar year
        - `limit` specifies the maximum number of results to retrieve.
        - `offset` specifies the number of results to skip before starting to fetch.
        """
        query = f'''
            from(bucket: "somebucket")
            |> range(start: 2023-01-15T00:00:00Z, stop: 2023-02-15T00:00:00Z)
            |> filter(fn: (r) => r._measurement == "o2_reading")
            |> pivot(rowKey:["_time"], columnKey: ["_field"], valueColumn: "_value")
            |> group(columns: ["_measurement", "_field", "units"])
            |> aggregateWindow(every: {unit}{dtype}, fn: mean, column:"value")
            |> limit(n:{limit}, offset:{offset})
        '''
        try:
            result = client.query_api().query(org="myorg", query=query)
        except ApiException:
            client = get_client()
            print("ApiException error happens retrying")
            continue

            # get_every(unit, dtype, limit, offset)
        jddata = []
        for i in result:
            for x in i:
                t = x.get_time()
                my_dict = {
                    "id": int(t.timestamp()),
                    "timestamp": t.timestamp(),
                    x.values.get("units"): x.values.get("value"),
                    "label": t.strftime("%d-%m-%Y %H:%M:%S")
                }
                jddata.append(my_dict)
        return jddata

if __name__ == "__main__":
    try:
        app.run(host="0.0.0.0", port=5000)
    except KeyboardInterrupt:
        print("i am exiting..")
        client.close()
        time.sleep(1)
