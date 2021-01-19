
import yaml
import re
from haversine import haversine, Unit
from car.target import Target

import logging

logger = logging.getLogger(__name__)

class TrackLocation:

    def __init__(self, name, lat1: float, long1: float, lat2: float, long2: float, dir):
        self.name = name
        start_finish_begin = (lat1, long1)
        start_finish_end = (lat2, long2)
        self.start_finish:Target = Target("start/finish", start_finish_begin, start_finish_end, dir)
        self.pit_in:Target = None
        self.radio_sync:Target = None

        logger.debug("{} : width = {} heading = {}".format(name, self.track_width_feet(),
                                                    int(self.start_finish.target_heading)))

    def track_width_feet(self):
        return int(haversine(self.start_finish.lat_long1, self.start_finish.lat_long2, unit=Unit.FEET))

    def get_target_heading(self):
        return self.start_finish.target_heading

    def get_start_finish_target(self) -> Target:
        return self.start_finish

    def is_pit_defined(self) -> bool:
        return self.pit_in is not None

    def get_pit_in_target(self) -> Target:
        return self.pit_in

    def set_pit_in_coords(self, lat_long1, lat_long2, direction):
        self.pit_in = Target("pit-in", lat_long1, lat_long2, direction)
        logger.debug("{} : pit-in heading = {}".format(self.name, int(self.pit_in.target_heading)))

    def is_radio_sync_defined(self) -> bool:
        return self.radio_sync is not None

    def get_radio_sync_target(self) -> Target:
        return self.radio_sync

    def set_radio_sync_coords(self, lat_long1, lat_long2, direction):
        self.radio_sync = Target("radio-sync", lat_long1, lat_long2, direction)
        logger.debug("{} : radio-sync heading = {}".format(self.name, int(self.radio_sync.target_heading)))

    def __repr__(self):
        return self.name


def read_tracks() -> [TrackLocation]:
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
            if "radio_sync_coords" in track:
                pi = track["radio_sync_coords"]
                points = re.findall("[-+]?\d+.\d+", pi)
                assert len(points) == 4, "expected 4 points"
                track_data.set_radio_sync_coords((float(points[0]), float(points[1])),
                                             (float(points[2]), float(points[3])), track["radio_sync_direction"])
            track_list.append(track_data)
    return track_list

if __name__ == "__main__":

    logging.basicConfig(format='%(asctime)s %(name)s %(message)s',
                        datefmt='%Y-%m-%d %H:%M:%S',
                        level=logging.DEBUG)

    read_tracks()
