from car.track import TrackLocation
from car.updaters import PositionUpdater, LapUpdater
from car.display_providers import LapProvider
from car.target import Target
from car.events import LeaveTrackEvent, CompleteLapEvent, RadioSyncEvent

from haversine import haversine, Unit
from car import geometry
import time
import logging

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


class LapTracker(PositionUpdater, LapProvider):

    def __init__(self, track: TrackLocation, listener: LapUpdater):
        self.track = track
        self.listener = listener
        self.on_track = False
        self.lap_start_time = 0.0
        self.last_pos = (0, 0)
        self.last_pos_time = 0.0
        self.lap_count = 999
        self.last_lap_time = 0
        self.last_pit_in_time = 0
        self.last_radio_sync_time = 0

    def update_position(self, lat:float, long:float, heading:float, time:float, speed:int) -> None:
        if (lat, long) == self.last_pos:
            return

        logger.debug("updating position to {} {}".format(lat, long))
        self.last_pos = (lat, long)
        if self.__crossed_line(lat, long, heading, self.track.start_finish):
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
                    self.last_lap_time = time - self.lap_start_time
                    if self.listener:
                        self.listener.update_lap(self.lap_count, self.last_lap_time)
                self.lap_start_time = time

        elif self.track.is_pit_defined() and \
            self.__crossed_line(lat, long, heading, self.track.pit_in):
            # de-bounce so that we don't re-enter the pits repeatedly
            # we could move the time into the target object,
            if time - self.last_pit_in_time > 30:
                self.on_track = False
                LeaveTrackEvent.emit()
                logger.info("entered pits")
                self.last_pit_in_time = time

        elif self.track.is_radio_sync_defined() and \
            self.__crossed_line(lat, long, heading, self.track.radio_sync):
            # de-bounce so that we don't re-enter the pits repeatedly
            # we could move the time into the target object,
            if time - self.last_radio_sync_time > 30:
                RadioSyncEvent.emit()
                logger.info("syncing radio")
                self.last_radio_sync_time = time

    def __crossed_line(self, lat, long, heading, target:Target):
        if angular_difference(target.target_heading, heading) > 20:
            return False

        dist = int(haversine(target.midpoint, (lat, long), unit=Unit.FEET))
        logger.debug("distance to target = {} feet".format(dist))
        if dist < 100:
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
                    logger.info("my heading = {}, target heading = {}".format(heading, target.target_heading))
                    return True
        return False

    def get_lap_count(self) -> int:
        return self.lap_count

    def get_lap_timer(self) -> int:
        return int(time.time() - self.lap_start_time)

    def get_last_lap_time(self) -> int:
        return self.last_lap_time

import csv
from car.track import read_tracks

if __name__ == "__main__":
    tracks = read_tracks()

    tracker = LapTracker(tracks[1], None)
    with open("../traces/trace-1608347418.csv") as csvfile:
        points = csv.reader(csvfile, quoting=csv.QUOTE_NONNUMERIC)
        x = 0
        for point in points:
            x += 1
            if x % 1 == 0:
                label = "hdg:{} spd:{}".format(int(point[3]), "?")
                tracker.update_position(point[1], point[2], point[3], point[0], 30)
