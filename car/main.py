
import time, os
from threading import Thread
from car.gui import Gui
from car.gps_reader import GpsReader
from car.maf_analyzer import MafAnalyzer
from car.obd_reader import ObdReader
from car.lap_tracker import LapTracker
from car.radio_interface import RadioInterface
from car.wifi import WifiManager
from car.display_providers import LocalTimeProvider
from car.track import TrackLocation, read_tracks
from car.state_machine import StateMachine
from car.movement_listener import MovementListener
from shared.radio import Radio
from shared.usb_detector import UsbDetector
from haversine import haversine
import logging
from logging.handlers import RotatingFileHandler
from datetime import datetime
from python_settings import settings

today = datetime.today().strftime('%Y-%m-%d')

logger = logging.getLogger(__name__)

# this enables console logging, but we're going to use
# rotating file based logging
logging.basicConfig(format='%(asctime)s %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S',
                    level=logging.WARN)

if not os.path.isdir("../logs"):
    os.mkdir("../logs")
file_handler = logging.FileHandler("logs/lap-logger-{}.csv".format(today))
lap_logger = logging.getLogger("lap-logger")
lap_logger.addHandler(file_handler)

handler = RotatingFileHandler("../logs/lemon-pi.log",
                              maxBytes=10000000,
                              backupCount=10)
handler.setFormatter(logging.Formatter(fmt='%(asctime)s %(message)s', datefmt='%Y-%m-%d %H:%M:%S'))
handler.setLevel(logging.INFO)
logging.getLogger().addHandler(handler)

logger.info("Lemon-Pi : starting up")

if not "SETTINGS_MODULE" in os.environ:
    os.environ["SETTINGS_MODULE"] = "config.settings-car"

# main control thread
# responsibilities
#  0. disable wifi (to save battery)
#  1. launch UI
#  2. fire up OBD thread
#  3. fire up GPS thread

WifiManager().disable_wifi()

state_machine = StateMachine()
movement_listener = MovementListener()

gui = Gui()

UsbDetector.init()

MA = MafAnalyzer(lap_logger)

tracks:[TrackLocation] = read_tracks()

# start a background thread to pull in gps data
gps = GpsReader()
gps.start()

# start a background thread to pull in OBD data
obd = ObdReader(MA)
obd.start()

# start a background thread to manage the radio function
radio = Radio(settings.RADIO_DEVICE, settings.RADIO_KEY)
radio.start()
# and the radio interface maps car events to and from the radio
radio_interface = RadioInterface(radio, obd, None, MA)
radio_interface.start()

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
    radio_interface.register_lap_provider(lap_tracker)

# fire up a transient thread that polls until a location fix happens,
# and then finds the closest track to our location
Thread(target=await_gps, daemon=True).start()

gui.register_speed_provider(gps)
gui.register_time_provider(LocalTimeProvider())
gui.register_temp_provider(obd)
gui.register_fuel_provider(MA)

gui.display()
