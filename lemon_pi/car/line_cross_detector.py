
from haversine import haversine, Unit

from lemon_pi.car import geometry
from lemon_pi.car.target import Target

import logging

logger = logging.getLogger(__name__)


class LineCrossDetector:

    def __init__(self, degrees=20):
        self.degrees = degrees
        self.last_timestamp = 0
        self.last_dist_to_line = 0
        self.line_in_front = False

    def reset(self):
        self.line_in_front = True
        self.last_dist_to_line = 0
        self.last_timestamp = 0

    def crossed_line(self, lat, long, heading, time: float, target: Target):
        if geometry.angular_difference(target.target_heading, heading) > self.degrees:
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
                if abs(heading - target_heading) > 160:

                    # elegant debounce I hope
                    if not self.line_in_front:
                        return False, 0

                    logger.debug("GONE PASSED {} line!!!!".format(target.name))
                    logger.debug("my heading = {}, target heading = {}".format(heading, target.target_heading))

                    # work out the precise time we crossed the line
                    if dist == 0.0 or self.last_timestamp == 0:
                        est_cross_time = time
                    else:
                        time_gap = time - self.last_timestamp
                        distance_ratio = (self.last_dist_to_line + dist) / dist
                        logger.debug("adjusting line cross time back by {:.3f}".format(time_gap / distance_ratio))
                        est_cross_time = time - (time_gap / distance_ratio)
                    # set ourselves up so that we were on the line
                    self.last_dist_to_line = 0
                    self.last_timestamp = est_cross_time
                    self.line_in_front = False
                    return True, est_cross_time

                # we're in front of the line, store the distance and the current time
                self.last_dist_to_line = dist
                self.last_timestamp = time
                self.line_in_front = True

        return False, 0
