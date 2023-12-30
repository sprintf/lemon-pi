import csv
import math

import gmplot
from secrets_do_not_checkin import gmap_apikey

gmap = gmplot.GoogleMapPlotter(39.539323, -122.331265, 17, map_type="satellite")
gmap.apikey=gmap_apikey


def calc_lateral_g(last_heading, this_heading, last_time, this_time, this_speed_mps):
    delta_heading = this_heading - last_heading
    if delta_heading > 180:
        delta_heading -= 360
    if delta_heading < -180:
        delta_heading += 360
    radian_delta = delta_heading * math.pi / 180
    return (this_speed_mps * radian_delta / (this_time - last_time)) / 9.81

with open("gps-2023-05-27.csv") as csvfile:
    rows = csv.reader(csvfile)
    x = 0
    lats = []
    longs = []
    timestamps = []
    speeds = []
    top_speed = 0
    last_speed = 0
    last_tstamp = 0
    last_heading = 0
    highest_accel_gforce = 0.6
    highest_decel_gforce = -0.7
    max_accel_gforce = 0
    max_decel_gforce = 0
    highest_left_g = 0
    highest_right_g = 0
    lateral_g_threshold = 1.25
    max_lateral_g = 0

    for row in rows:
        tstamp = float(row[1])
        lap = int(row[2])
        lat = float(row[3])
        long = float(row[4])
        speed = int(row[5])
        heading = int(row[6])

        if last_speed > 0 and speed > 0:
            speed_mps = speed / 2.237
            last_speed_mps = last_speed / 2.237
            g_force = ((speed_mps - last_speed_mps) / (tstamp - last_tstamp)) / 9.81
            if g_force >= highest_accel_gforce:
                print(f"got high acceleration gforce of {g_force} on lap {lap} at {tstamp}")
            if g_force > max_accel_gforce:
                max_accel_gforce = g_force
            if g_force <= highest_decel_gforce:
                print(f"got high deceleration gforce of {g_force} on lap {lap} at {tstamp}")
                gmap.marker(lat, long, color="red")
            if g_force < highest_decel_gforce:
                max_decel_gforce = g_force

            if speed > 30:
                lateral_g = calc_lateral_g(last_heading, heading, last_tstamp, tstamp, speed_mps)
                if (abs(lateral_g) > lateral_g_threshold):
                    print(f"got high lateral g of {lateral_g} {last_heading} {heading} {speed_mps}")
                    gmap.marker(lat, long, color="yellow")
                if abs(lateral_g) > max_lateral_g:
                    max_lateral_g = abs(lateral_g)


        last_speed = speed
        last_heading = heading
        last_tstamp = tstamp

print(f"found max acceleration g_force is {max_accel_gforce}")
print(f"found max deceleration g_force is {max_decel_gforce}")
print(f"found max lateral g_force is {max_lateral_g}")

gmap.draw("mymap.html")








