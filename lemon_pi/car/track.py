
import yaml
import re
from haversine import haversine, Unit

from lemon_pi.car.update_tracks import TrackUpdater
from lemon_pi.car.event_defs import LeaveTrackEvent, RadioSyncEvent, EnterTrackEvent
from lemon_pi.car.target import Target

import logging

logger = logging.getLogger(__name__)


class TargetMetaData:

    def __init__(self, field_name, file_field_name, event):
        self.field_name = field_name
        self.file_field_name = file_field_name
        self.event = event


START_FINISH = TargetMetaData("start_finish", "start_finish", None)
PIT_ENTRY = TargetMetaData("pit_in", "pit_entry", LeaveTrackEvent)
PIT_OUT = TargetMetaData("pit_out", "pit_out", EnterTrackEvent)
RADIO_SYNC = TargetMetaData("radio_sync", "radio_sync", RadioSyncEvent)


TARGETS = [START_FINISH, PIT_ENTRY, PIT_OUT, RADIO_SYNC]


class TrackLocation:

    def __init__(self, name):
        self.name = name
        self.targets:{TargetMetaData, Target} = {}
        self.hidden = False

    def get_display_name(self):
        # name hidden tracks with an _ at the end of their name
        return "{}_".format(self.name) if self.hidden else self.name

    def track_width_feet(self):
        sf = self.get_start_finish_target()
        return int(haversine(sf.lat_long1, sf.lat_long2, unit=Unit.FEET))

    def get_target_heading(self):
        return self.get_start_finish_target().target_heading

    def get_start_finish_target(self) -> Target:
        return self.targets[START_FINISH]

    def set_start_finish_target(self, t:Target):
        self.targets[START_FINISH] = t

    def is_pit_defined(self) -> bool:
        return self.targets.get(PIT_ENTRY) is not None

    def get_pit_in_target(self) -> Target:
        return self.targets[PIT_ENTRY]

    def set_pit_in_target(self, t:Target):
        self.targets[PIT_ENTRY] = t

    def is_pit_out_defined(self) -> bool:
        return self.targets.get(PIT_OUT) is not None

    def get_pit_out_target(self) -> Target:
        return self.targets[PIT_OUT]

    def is_radio_sync_defined(self) -> bool:
        return self.targets.get(RADIO_SYNC) is not None

    def get_radio_sync_target(self) -> Target:
        return self.targets[RADIO_SYNC]

    def set_radio_sync_target(self, t:Target):
        self.targets[RADIO_SYNC] = t

    def __repr__(self):
        return self.name


def read_tracks() -> [TrackLocation]:
    track_list = []
    track_file, _ = TrackUpdater.get_track_file()
    with open(track_file) as yamlfile:
        tracks = yaml.load(yamlfile, Loader=yaml.FullLoader)
        for track in tracks["tracks"]:
            track_data = TrackLocation(track["name"])

            for tmd in TARGETS:
                if track.get(tmd.file_field_name + "_coords"):
                    coords = track[tmd.file_field_name + "_coords"]
                    points = re.findall("[-+]?\d+.\d+", coords)
                    assert len(points) == 4, "expected 4 points"
                    target = Target(tmd.field_name,
                                    (float(points[0]), float(points[1])),
                                    (float(points[2]), float(points[3])),
                                    track[tmd.file_field_name + "_direction"])
                    track_data.targets[tmd] = target

            # we must have a start/finish .. everything else is optional
            assert track_data.targets[START_FINISH]

            if "hidden" in track and track["hidden"]:
                track_data.hidden = True

            track_list.append(track_data)
    return track_list

if __name__ == "__main__":
    print(len(read_tracks()))
