
# a target is a point on the track that we want to head to
# it is defined as being two lat_longs defining the endpoints
# of a line. And a heading that indicates a tangent to the
# direction of travel when passing the point.
from lemon_pi.car.geometry import calc_intersect_heading


class Target:

    def __init__(self, name, lat_long1, lat_long2, direction="", target_heading=0):
        self.name = name
        self.lat_long1 = min(lat_long1, lat_long2)
        self.lat_long2 = max(lat_long1, lat_long2)
        if direction:
            self.target_heading = calc_intersect_heading(self.lat_long1, self.lat_long2, direction)
        else:
            self.target_heading = target_heading
        self.midpoint = self._calc_midpoint_()

    def _calc_midpoint_(self):
        lat1, long1 = self.lat_long1
        lat2, long2 = self.lat_long2
        return (lat1 + lat2) / 2.0, (long1 + long2) / 2.0