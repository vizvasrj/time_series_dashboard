query = '''
    from(bucket: "somebucket")
    |> range(start: -270d, stop: -269d)
    |> filter(fn: (r) => r._measurement == "o2_reading")
    |> pivot(rowKey:["_time"], columnKey: ["_field"], valueColumn: "_value")
    |> group(columns: ["_measurement", "_field"])
    |> aggregateWindow(every: 20s, fn: mean, column:"value")
    |> limit(n:10)
'''
result = client.query_api().query(org="myorg", query=query)