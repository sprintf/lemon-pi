import csv
import gmplot
import secrets

gmap = gmplot.GoogleMapPlotter(38.1589, -122.4536, 17, map_type="satellite")
gmap.apikey=secrets.gmap_apikey

target_lap = 13

with open("gps-2021-08-21.csv") as csvfile:
    rows = csv.reader(csvfile)
    x = 0
    lats = []
    longs = []
    timestamps = []
    speeds = []
    top_speed = 0
    for row in rows:
        tstamp = float(row[1])
        lap = int(row[2])
        lat = float(row[3])
        long = float(row[4])
        speed = int(row[5])
        heading = int(row[6])

        if lap == target_lap and speed > 0:
            timestamps.append(tstamp)
            lats.append(lat)
            longs.append(long)
            speeds.append(speed)
            top_speed = max(top_speed, speed)

print(f"found {len(lats)} points for lap {target_lap}")
gmap.plot(lats, longs, color='purple', size=len(lats))
lap_time = timestamps[-1] - timestamps[0]
print(f"lap time = {lap_time:.3f}")
mins = int(lap_time / 60)
secs = int(lap_time % 60)
msec = int((lap_time - (mins * 60) - secs) * 1000)
gmap.text(lats[0], longs[0], f"lap: {target_lap} time: {mins}:{secs:02}.{msec} top speed = {top_speed} mph", color="yellow")
top_speed_index = speeds.index(top_speed)
gmap.marker(lats[top_speed_index], longs[top_speed_index], title=f"{top_speed} mph")
gmap.draw("mymap.html")




