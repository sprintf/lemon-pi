from lemon_pi.car.track import TrackLocation, START_FINISH
from lemon_pi.car.updaters import PositionUpdater, LapUpdater
from lemon_pi.car.display_providers import LapProvider
from lemon_pi.car.target import Target
from lemon_pi.car.event_defs import (
    LeaveTrackEvent,
    CompleteLapEvent,
    RadioSyncEvent,
    LapInfoEvent, EnterTrackEvent
)

from haversine import haversine, Unit
from lemon_pi.car import geometry
import time
import logging

from lemon_pi.shared.events import EventHandler

logger = logging.getLogger(__name__)


def angular_difference(h1, h2):
    diff = abs(h1 - h2)
    if diff > 180:
        if h1 < 180:
            h1 = h1 + 360
        else:
            h2 = h2 + 360
        diff = abs(h1 - h2)
    return diff


class LapTracker(PositionUpdater, LapProvider, EventHandler):

    def __init__(self, track: TrackLocation, listener: LapUpdater):
        self.track = track
        self.listener = listener
        self.on_track = False
        self.lap_start_time = time.time()
        self.last_pos = (0, 0)
        self.last_pos_time = 0.0
        self.lap_count = 999
        self.last_lap_time = 0
        self.last_timestamp = 0
        self.last_dist_to_line = 0
        LapInfoEvent.register_handler(self)
        LeaveTrackEvent.register_handler(self)
        EnterTrackEvent.register_handler(self)

    def update_position(self, lat:float, long:float, heading:float, time:float, speed:int) -> None:
        if (lat, long) == self.last_pos:
            return

        logger.debug("updating position to {} {}".format(lat, long))
        self.last_pos = (lat, long)
        crossed_line, cross_time = self._crossed_line(lat, long, heading, time, self.track.get_start_finish_target())
        if crossed_line:
            # de-bounce hitting start finish line twice ... a better
            # approach might be to ensure car travels so far away from line
            if time - self.lap_start_time > 10:
                CompleteLapEvent.emit()
                if not self.on_track:
                    logger.info("entering track")
                    # this isn't true for a multi-driver day, but we'll keep each
                    # drivers view as their own
                    self.lap_count = 0
                    self.on_track = True
                    if self.listener:
                        self.listener.update_lap(0, 0)
                else:
                    logger.info("completed lap!")
                    self.lap_count += 1
                    self.last_lap_time = cross_time - self.lap_start_time
                    if self.listener:
                        self.listener.update_lap(self.lap_count, self.last_lap_time)
                self.lap_start_time = cross_time

                if not self.track.is_radio_sync_defined():
                    RadioSyncEvent.emit(ts=cross_time)
        else:
            for target_metadata in self.track.targets.keys():
                target = self.track.targets[target_metadata]
                if target_metadata != START_FINISH:
                    crossed_target, cross_time = self._crossed_line(lat, long, heading, time, target)
                    if crossed_target:
                        target_metadata.event.emit(ts=cross_time)

    def handle_event(self, event, lap_count=0, ts=0):
        if event == LapInfoEvent:
            # the lap info tells us the last lap completed, but this
            # lap timer is showing the next lap, so we add one to it
            self.lap_count = lap_count + 1

            # this only gets hit in simulation mode when the car is not
            # actually running. It lets us see some lap time data when
            # testing out a pre-recorded feed
            if not self.on_track:
                self.last_lap_time = ts - self.lap_start_time
                self.lap_start_time = ts
        if event == LeaveTrackEvent:
            self.on_track = False
        if event == EnterTrackEvent:
            self.on_track = True
            self.lap_start_time = ts

    def _crossed_line(self, lat, long, heading, time:float, target:Target):
        if angular_difference(target.target_heading, heading) > 20:
            return False, 0

        dist = int(haversine(target.midpoint, (lat, long), unit=Unit.FEET))
        logger.debug("distance to target = {} feet".format(dist))
        # needs to be 200 feet or less. At 100mph a car covers 150 feet per second, and
        # some gps devices are only providing updates once per second
        if dist < 200:
            # grab a point that we're heading towards
            point_ahead = geometry.get_point_on_heading((lat, long), heading)

            # work out the intersect from car to line
            intersect = geometry.seg_intersect_lat_long(target.lat_long1, target.lat_long2,
                                                        (lat, long), point_ahead)

            # is this intersect point on the target line?
            if geometry.is_between(target.lat_long1, target.lat_long2, intersect):
                logger.debug("on track to hit target")

                # lets get the heading from our current position to the intersect
                target_heading = geometry.heading_between_lat_long((lat, long), intersect)
                if (abs(heading - target_heading) > 160):
                    logger.info("GONE PASSED {} line!!!!".format(target.name))
                    logger.debug("my heading = {}, target heading = {}".format(heading, target.target_heading))

                    # work out the precise time we crossed the line
                    time_gap = time - self.last_timestamp
                    distance_ratio = (self.last_dist_to_line + dist) / dist
                    logger.debug("adjusting line cross time back by {:.3f}".format(time_gap / distance_ratio))
                    est_cross_time = time - (time_gap / distance_ratio)

                    return True, est_cross_time

                # we're in front of the line, store the distance and the current time
                self.last_dist_to_line = dist
                self.last_timestamp = time
        return False, 0

    def get_lap_count(self) -> int:
        return self.lap_count

    def get_lap_timer(self) -> int:
        return int(time.time() - self.lap_start_time)

    def get_last_lap_time(self) -> float:
        return self.last_lap_time

import csv
from lemon_pi.car.track import read_tracks

logger = logging.getLogger(__name__)

logging.basicConfig(format='%(asctime)s %(name)s %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S',
                    level=logging.DEBUG)

if __name__ == "__main__":
    tracks = read_tracks()

    tracker = LapTracker(tracks[1], None)
    with open("traces/trace-1608347418.csv") as csvfile:
        points = csv.reader(csvfile, quoting=csv.QUOTE_NONNUMERIC)
        x = 0
        for point in points:
            x += 1
            if x % 1 == 0:
                label = "hdg:{} spd:{}".format(int(point[3]), "?")
                tracker.update_position(point[1], point[2], point[3], point[0], 30)
