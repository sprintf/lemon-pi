import csv
import gmplot

from lemon_pi.car.drs_controller import DrsDataLoader
from secrets_do_not_checkin import gmap_apikey as api_key

gmap = gmplot.GoogleMapPlotter(39.539323, -122.331265, 17, map_type="satellite")
gmap.apikey=api_key

target_lap = 91

loader = DrsDataLoader()
loader.read_file("resources/drs_zones.json")
thil_drs_zones = loader.get_drs_activation_zones("thil")

with open("gps-2023-05-27.csv") as csvfile:
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

for gate in thil_drs_zones:
    lats = [gate.target.lat_long1[0], gate.target.lat_long2[0]]
    longs = [gate.target.lat_long1[1], gate.target.lat_long2[1]]
    gmap.plot(lats, longs, color='blue', size=len(lats))

gmap.draw("mymap.html")




