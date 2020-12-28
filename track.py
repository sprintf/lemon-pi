
import yaml
import re
from haversine import haversine, Unit
from geometry import calc_intersect_heading
from target import Target

class TrackLocation:

    def __init__(self, name, lat1: float, long1: float, lat2: float, long2: float, dir):
        self.name = name
        start_finish_begin = (lat1, long1)
        start_finish_end = (lat2, long2)
        direction = dir
        target_heading = calc_intersect_heading(start_finish_begin, start_finish_end, direction)
        self.start_finish:Target = Target(start_finish_begin, start_finish_end, target_heading)
        self.pit_in:Target = None

        print("{} {}".format(self.track_width(), target_heading))

    def track_width(self):
        return haversine(self.start_finish.lat_long1, self.start_finish.lat_long2, unit=Unit.FEET)

    def get_target_heading(self):
        return self.target_heading

    def get_start_finish_target(self) -> Target:
        return self.start_finish

    def is_pit_defined(self) -> bool:
        return self.pit_in is not None

    def get_pit_in_target(self) -> Target:
        return self.pit_in

    def set_pit_in_coords(self, lat_long1, lat_long2, direction):
        pit_in_heading = calc_intersect_heading(lat_long1, lat_long2, direction)
        self.pit_in = Target(lat_long1, lat_long2, pit_in_heading)

    def __repr__(self):
        return self.name


def read_tracks():
    track_list = []
    with open("resources/tracks.yaml") as yamlfile:
        tracks = yaml.load(yamlfile, Loader=yaml.FullLoader)
        for track in tracks["tracks"]:
            sf = track["start_finish_coords"]
            points = re.findall("[-+]?\d+.\d+", sf)
            assert len(points) == 4, "expected 4 points"
            track_data = TrackLocation(track["name"], float(points[0]), float(points[1]), float(points[2]),
                                     float(points[3]), track["start_finish_direction"])
            if "pit_entry_coords" in track:
                pi = track["pit_entry_coords"]
                points = re.findall("[-+]?\d+.\d+", pi)
                assert len(points) == 4, "expected 4 points"
                track_data.set_pit_in_coords((float(points[0]), float(points[1])),
                                             (float(points[2]), float(points[3])), track["pit_entry_direction"])
            track_list.append(track_data)
    return track_list

if __name__ == "__main__":
    read_tracks()
