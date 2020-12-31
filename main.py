
import time, os
from threading import Thread
from gui import Gui
from gps_reader import GpsReader
from maf_analyzer import MafAnalyzer
from obd_reader import ObdReader
from lap_tracker import LapTracker
from display_providers import TimeProvider
from track import TrackLocation, read_tracks
from state_machine import StateMachine
from movement_listener import MovementListener
from haversine import haversine
import logging

logger = logging.getLogger(__name__)
logging.basicConfig(format='%(asctime)s %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S',
                    level=logging.INFO)

logger.info("starting up")

# main control thread
# responsibilities
#  1. launch UI
#  2. fire up OBD thread
#  3. fire up GPS thread

state_machine = StateMachine()
movement_listener = MovementListener()

gui = Gui()


class LocalTimeProvider(TimeProvider):

    def get_hours(self) -> int:
        return int(time.time() / 3600 - 8) % 12

    def get_minutes(self) -> int:
        return int(time.time() / 60) % 60

    def get_seconds(self) -> int:
        return int(time.time()) % 60


if not os.path.isdir("logs"):
    os.mkdir("logs")
file_handler = logging.FileHandler("logs/lap-logger-{}.csv".format(int(time.time())))
lap_logger = logging.getLogger("lap-logger")
lap_logger.addHandler(file_handler)
MA = MafAnalyzer(lap_logger)

tracks:[TrackLocation] = read_tracks()

# start a background thread to pull in gps data
gps = GpsReader()
gps.start()

# start a background thread to pull in OBD data
obd = ObdReader(MA)
obd.start()

# store the closest track
closest_track: TrackLocation = None

def await_gps():
    logger.info("awaiting location to choose track")
    while not gps.is_working() or gps.get_lat_long() == (0, 0):
        time.sleep(1)
    global closest_track
    closest_track = min(tracks, key=lambda x: haversine(gps.get_lat_long(), x.start_finish.midpoint))
    logger.info("closest track selected : {}".format(closest_track))
    lap_tracker = LapTracker(closest_track, MA)
    gps.register_position_listener(lap_tracker)
    gui.register_lap_provider(lap_tracker)

# fire up a transient thread that polls until a location fix happens,
# and then finds the closest track to our location
Thread(target=await_gps, daemon=True).start()

gui.register_speed_provider(gps)
gui.register_time_provider(LocalTimeProvider())
gui.register_temp_provider(obd)
gui.register_fuel_provider(MA)

gui.display()
