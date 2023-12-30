from typing import Optional


class GpsPos:
    def __init__(self, lat: float, long: float, heading: int, speed: float, timestamp: float):
        self.lat = lat
        self.long = long
        self.heading = heading
        self.speed = speed
        self.timestamp = timestamp


class GpsProvider:

    # returns None if there's nothing up to date
    def get_gps_position(self) -> Optional[GpsPos]:
        pass
