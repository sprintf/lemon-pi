import csv
import gmplot
import secrets

gmap = gmplot.GoogleMapPlotter(37.928, -122.299, 16)
gmap.apikey=secrets.gmap_apikey

with open("../../traces/trace-1608347418.csv") as csvfile:
    points = csv.reader(csvfile, quoting=csv.QUOTE_NONNUMERIC)
    x = 0
    for point in points:
        x += 1
        if x % 10 == 0:
            label = "hdg:{} spd:{}".format(int(point[3]),"?")
            gmap.marker(point[1], point[2], label=label)

gmap.draw("mymap.html")




