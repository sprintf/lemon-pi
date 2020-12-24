
import time
from threading import Thread
from gui import Gui
from gps_reader import GpsReader
from maf_analyzer import MA
from obd_reader import ObdReader
from lap_tracker import LapTracker
from display_providers import TemperatureProvider
from display_providers import TimeProvider
from display_providers import SpeedProvider
from track import TrackLocation, read_tracks
import logging

logger = logging.getLogger(__name__)
logging.basicConfig(format='%(asctime)s %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p')

logger.info("starting up")

# main control thread
# responsibilities
#  1. launch UI
#  2. fire up OBD thread
#  3. fire up GPS thread

gui = Gui()

class LocalTimeProvider(TimeProvider):

    def get_hours(self) -> int:
        return int(time.time() / 3600 - 8) % 12

    def get_minutes(self) -> int:
        return int(time.time() / 60) % 60

    def get_seconds(self) -> int:
        return int(time.time()) % 60


class LocalTempProvider(TemperatureProvider):

    def get_temp_f(self) -> int:
        return 185


class LocalSpeedProvider(SpeedProvider):

    def __init__(self):
        self.speed = 25
        self.incr = +2

    def getSpeed(self) -> int:
        self.speed += self.incr
        if self.speed >= 104:
            self.incr = -1
        if self.speed < 25:
            self.incr = +1
        return self.speed


tracks = read_tracks()

gps = GpsReader()
gps.start()

obd = ObdReader()
obd.start()

closest_track: TrackLocation = None

def await_gps():
    logger.info("awaiting location to choose track")
    while not gps.is_working() or gps.get_lat_long() == (0, 0):
        time.sleep(1)
    global closest_track
    closest_track = tracks[5]
    logger.info("closest track selected : {}".format(closest_track))
    lap_tracker = LapTracker(closest_track)
    gps.register_position_listener(lap_tracker)
    gui.register_lap_provider(lap_tracker)


Thread(target=await_gps).start()

gui.register_speed_provider(gps)
gui.register_time_provider(LocalTimeProvider())
gui.register_temp_provider(obd)
gui.register_fuel_provider(MA)

gui.display()
