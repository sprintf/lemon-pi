import csv
import gmplot
from secrets_do_not_checkin import gmap_apikey

# gmap = gmplot.GoogleMapPlotter(38.1589, -122.4536, 17, map_type="satellite")
gmap = gmplot.GoogleMapPlotter(39.539323, -122.331265, 17, map_type="satellite")
gmap.apikey=gmap_apikey

target_lap = 150

old_top_speeds = [0, 29.4, 48.0, 68.7, 87.7, 111]
new_top_speeds = [0, 32.1, 52.3, 74.9, 95.5, 121]


def changed_gear(last_speed, speed, shift_speeds):
    for pos, shift_speed in enumerate(shift_speeds):
        if last_speed < shift_speed and speed >= shift_speed:
            return pos + 1
    return 0


with open("gps-2023-05-27.csv") as csvfile:
    rows = csv.reader(csvfile)
    x = 0
    lats = []
    longs = []
    timestamps = []
    speeds = []
    old_gear_change_count = 0
    new_gear_change_count = 0
    gear_change_points = []
    top_speed = 0
    last_speed = 0
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

            gear = changed_gear(last_speed, speed, old_top_speeds)
            if gear:
                old_gear_change_count += 1
                gear_change_points.append((lat, long, "lightblue", gear))

            gear = changed_gear(last_speed, speed, new_top_speeds)
            if gear:
                new_gear_change_count += 1
                gear_change_points.append((lat, long, "white", gear))

        last_speed = speed

print(f"found {len(lats)} points for lap {target_lap}")
gmap.plot(lats, longs, color='purple', size=len(lats))
lap_time = timestamps[-1] - timestamps[0]
print(f"lap time = {lap_time:.3f}")
mins = int(lap_time / 60)
secs = int(lap_time % 60)
msec = int((lap_time - (mins * 60) - secs) * 1000)
# gmap.text(lats[0], longs[0], f"lap: {target_lap} time: {mins}:{secs:02}.{msec} top speed = {top_speed} mph", color="yellow")
for (lat, long, color, gear) in gear_change_points:
    gmap.marker(lat, long, color=color, draggable=True, label=str(gear))
print(f"old gear changes per lap = {old_gear_change_count * 2}")
print(f"new gear changes per lap = {new_gear_change_count * 2}")
top_speed_index = speeds.index(top_speed)
# gmap.marker(lats[top_speed_index], longs[top_speed_index], title=f"{top_speed} mph")
gmap.draw("mymap.html")

# 14 shifts (28 w/ ups and downs)  new ratio
# 14 shifts (28 w/ ups and downs) old ratio





