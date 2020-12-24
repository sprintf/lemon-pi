
import csv
from haversine import haversine, Unit
from numpy import arctan2,random,sin,cos,degrees

class TrackLocation:

    def __init__(self, name, x1: float, y1: float, x2: float, y2: float, dir):
        self.name = name
        self.start_finish_begin = (x1, y1)
        self.start_finish_end = (x2, y2)
        self.direction = dir
        self.target_heading = self.calc_start_finish_heading()

        print("{} {}".format(self.track_width(), self.target_heading))

    def track_width(self):
        return haversine(self.start_finish_begin, self.start_finish_end, unit=Unit.FEET)
        # x1, y1 = self.start_finish_begin
        # x2, y2 = self.start_finish_end
        # xdiff = abs(x1 - x2)
        # ydiff = abs(y1 - y2)
        # return math.sqrt((xdiff * xdiff) + (ydiff * ydiff))

    def get_target_heading(self):
        return self.target_heading

    def start_finish_midpoint(self):
        lat1, long1 = self.start_finish_begin
        lat2, long2 = self.start_finish_end
        return ((lat1 + lat2) / 2, (long1 + long2) / 2)

    def calc_start_finish_heading(self):
        a = self.start_finish_begin
        b = self.start_finish_end
        lat = 0
        lon = 1

        dL = b[lon] - a[lon]
        X = cos(b[lat]) * sin(dL)
        Y = cos(a[lat]) * sin(b[lat]) - sin(a[lat]) * cos(b[lat]) * cos(dL)
        line_heading = degrees(arctan2(X, Y))
        # todo : based on "S", "SW", etc this might be +90 or +180
        rotation = 90
        if "E" in self.direction or "N" in self.direction:
            rotation = -90
        return (line_heading + rotation) % 360

    def __repr__(self):
        return self.name


def read_tracks():
    track_list = []
    with open("resources/tracks.csv") as csvfile:
        tracks = csv.reader(csvfile, quoting=csv.QUOTE_NONNUMERIC)
        # skip the header
        next(tracks)
        for track in tracks:
            track_list.append(TrackLocation(track[0], track[1], track[2], track[3], track[4], track[5]))
    return track_list

if __name__ == "__main__":
    read_tracks()
