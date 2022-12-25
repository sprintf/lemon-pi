

class GpsPos:
    def __init__(self, lat, long, heading, speed, timestamp):
        self.lat = lat
        self.long = long
        self.heading = heading
        self.speed = speed
        self.timestamp = timestamp


class GpsProvider:

    # returns None if there's nothing up to date
    def get_gps_position(self) -> GpsPos:
        pass
