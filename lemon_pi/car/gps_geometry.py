

# returns a boolean indicating if the car has crossed the target. If it has, it also returns the
# estimated time that the car crossed the line, and a flag indicating if the car is going in the
# wrong direction
import logging
from typing import Optional

from haversine import haversine, Unit

from lemon_pi.car.geometry import seg_intersect_lat_long, is_between, heading_between_lat_long, angular_difference, \
    get_point_on_heading
from lemon_pi.car.target import Target
from lemon_pi.shared.data_provider_interface import GpsPos

logger = logging.getLogger(__name__)


def crossed_line(last_pos: Optional[GpsPos], this_pos: GpsPos, target: Target) -> (bool, float, bool):
    if last_pos is None:
        return False, 0, False

    dist = int(haversine(target.midpoint, (this_pos.lat, this_pos.long), unit=Unit.FEET))

    logger.debug(f"distance to {target.name} target = {dist} feet")
    # needs to be 200 feet or less. At 100mph a car covers 150 feet per second, and
    # some gps devices are only providing updates once per second
    if dist < 200:
        # work out the intersect from car to line
        intersect = seg_intersect_lat_long(
            target.lat_long1,
            target.lat_long2,
            (last_pos.lat, last_pos.long),
            (this_pos.lat, this_pos.long))

        # is this intersect point on the target line?
        if is_between(target.lat_long1, target.lat_long2, intersect) and \
           is_between((last_pos.lat, last_pos.long), (this_pos.lat, this_pos.long), intersect):
            logger.debug("pretty sure line crossed")

            # lets get the heading from our current position to the intersect
            target_heading = heading_between_lat_long((this_pos.lat, this_pos.long), intersect)
            last_target_heading = heading_between_lat_long((last_pos.lat, last_pos.long), intersect)
            if abs(last_target_heading - target_heading) > 150:

                crossed_backwards = angular_difference(this_pos.heading, target.target_heading) > 150
                logger.debug(f"angular difference = {angular_difference(this_pos.heading, target.target_heading)}")

                logger.debug("GONE PASSED {} line!!!!".format(target.name))
                logger.debug("my heading = {}, target heading = {}".format(this_pos.heading, target.target_heading))

                # work out the precise time we crossed the line
                if dist == 0.0:
                    est_cross_time = this_pos.timestamp
                else:
                    time_gap = this_pos.timestamp - last_pos.timestamp
                    last_dist = int(haversine(target.midpoint, (last_pos.lat, last_pos.long), unit=Unit.FEET))
                    distance_ratio = (last_dist + dist) / dist
                    logger.debug("adjusting line cross time back by {:.3f}".format(time_gap / distance_ratio))
                    est_cross_time = this_pos.timestamp - (time_gap / distance_ratio)
                # set ourselves up so that we were on the line
                return True, est_cross_time, crossed_backwards

    return False, 0, False


# will we cross the line associated with the given target in the next second or so?
def will_cross_line(this_pos: GpsPos, target: Target) -> (bool, float, bool):
    # how far away will we be in 1.25 second if we carry on this heading?
    # why 1.25s ? well gps pulses at 1s, but under acceleration we cover more
    # distance than we'd expect in a second creating gaps that cause us to miss gates
    miles_per_sec = this_pos.speed / 3600
    miles_per_2s = miles_per_sec * 1.8
    next_lat_long = get_point_on_heading((this_pos.lat, this_pos.long), this_pos.heading, miles_per_2s)
    next_gps_point = GpsPos(next_lat_long[0], next_lat_long[1],
                            this_pos.heading, this_pos.speed, this_pos.timestamp + 1.8)
    if this_pos.speed > 10:
        logger.info(f"this gps point = {this_pos.lat},{this_pos.long} travelling at {miles_per_sec} mps")
        logger.info(f"next gps point = {next_lat_long[0]},{next_lat_long[1]}")
        dist1 = haversine((this_pos.lat, this_pos.long), target.midpoint, Unit.FEET)
        dist2 = haversine(next_lat_long, target.midpoint, Unit.FEET)
        logger.info(f"dist to this = {dist1}    dist to next = {dist2}")

    (crossed, cross_time, backwards) = crossed_line(this_pos, next_gps_point, target)
    if target.target_heading < 0:
        target.target_heading = this_pos.heading
    return crossed, cross_time, False
