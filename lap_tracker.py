from track import TrackLocation
from updaters import PositionUpdater, LapUpdater
from display_providers import LapProvider
from target import Target

from haversine import haversine, Unit
import geometry
import time
import logging

logger = logging.getLogger(__name__)

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

    def update_position(self, lat:float, long:float, heading:float, time:float, speed:int) -> None:
        if (lat, long) == self.last_pos:
            return

        logger.debug("updating position to {} {}".format(lat, long))
        self.last_pos = (lat, long)
        if self.__crossed_line(lat, long, heading, self.track.start_finish):
            # de-bounce hitting start finish line twice ... a better
            # approach might be to ensure car travels so far away from line
            if time - self.lap_start_time > 10:
                if not self.on_track:
                    logger.info("entering track")
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
            self.__crossed_line__(self, lat, long, heading, self.track.pit_in):
            logger.info("entered pits")

    def __crossed_line(self, lat, long, heading, target:Target):
        if self.angular_difference(target.target_heading(), heading) > 15:
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
                if (abs(heading - target_heading) > 170):
                    logger.info("GONE PASSED start/finish line!!!!")
                    return True
        return False

    def angular_difference(self, h1, h2):
        if h1 > 180:
            h1 = h1 - 180
        if h2 > 180:
            h2 = h2 - 180
        logger.debug("angular diff = {}".format(abs(h1 - h2)))
        return abs(h1 - h2)

    def get_lap_count(self) -> int:
        return self.lap_count

    def get_lap_timer(self) -> int:
        return int(time.time() - self.lap_start_time)

    def get_last_lap_time(self) -> int:
        return self.last_lap_time

import csv
from track import read_tracks

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
