import os
from statistics import stdev

from haversine import haversine
from haversine import Unit

from lemon_pi.car.gps_reader import GpsReader
from lemon_pi.car.updaters import PositionUpdater
from lemon_pi.shared.usb_detector import UsbDetector

# a spot in the middle of the back garden
(target_lat, target_long) = (37.92830813674162, -122.29757847246408)


class VarianceObserver(PositionUpdater):

    def __init__(self):
        self.total_error = 0
        self.recent_samples = []
        self.loop = 0

    def update_position(self, lat: float, long: float, heading: float, time: float, speed: int) -> None:
        error = haversine((lat, long), (target_lat, target_long), unit=Unit.FEET)
        self.total_error += error
        self.loop += 1
        self.recent_samples.append(error)
        if len(self.recent_samples) > 100:
            self.recent_samples.pop(0)
            recent_average = int(sum(self.recent_samples) / len(self.recent_samples))
            stddev= stdev(self.recent_samples[0::10])
            if self.loop % 10 == 0:
                print(f"{self.loop}s recent error = {recent_average} with {stddev}\n")


if __name__ == "__main__":

    if "SETTINGS_MODULE" not in os.environ:
        os.environ["SETTINGS_MODULE"] = "lemon_pi.config.local_settings_car"

    UsbDetector.init()
    tracker = GpsReader()
    tracker.call_gpsctl()
    tracker.register_position_listener(VarianceObserver())
    tracker.run()
