from typing import Optional


class GpsPos:
    def __init__(self, lat: float, long: float, heading: float, speed: int, timestamp: float):
        self.lat: float = lat
        self.long: float = long
        self.heading: float = heading
        self.speed: int = speed
        self.timestamp: float = timestamp


class GpsProvider:

    # returns None if there's nothing up to date
    def get_gps_position(self) -> Optional[GpsPos]:
        pass
