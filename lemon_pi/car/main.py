
import time, os
from threading import Thread

from lemon_pi.car.audio import Audio
from lemon_pi.car.button import Button
from lemon_pi.car.event_defs import ExitApplicationEvent
from lemon_pi.car.gui import Gui
from lemon_pi.car.gps_reader import GpsReader
from lemon_pi.car.lap_session_store import LapSessionStore
from lemon_pi.car.maf_analyzer import MafAnalyzer
from lemon_pi.car.obd_reader import ObdReader
from lemon_pi.car.lap_tracker import LapTracker
from lemon_pi.car.radio_interface import RadioInterface
from lemon_pi.car.update_tracks import TrackUpdater
from lemon_pi.car.wifi import WifiManager
from lemon_pi.shared.meringue_comms import MeringueComms
from lemon_pi_pb2 import ToCarMessage
from lemon_pi.shared.time_provider import LocalTimeProvider
from lemon_pi.car.track import TrackLocation, read_tracks
from lemon_pi.car.state_machine import StateMachine
from lemon_pi.car.movement_listener import MovementListener
from lemon_pi.shared.radio import Radio
from lemon_pi.shared.usb_detector import UsbDetector
from haversine import haversine
import logging
from logging.handlers import RotatingFileHandler
from datetime import datetime
from python_settings import settings

today = datetime.today().strftime('%Y-%m-%d')

logger = logging.getLogger(__name__)

# this enables console logging, but we're going to use
# rotating file based logging
logging.basicConfig(format='%(asctime)s.%(msecs)03d %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S',
                    level=logging.WARN)

if not os.path.isdir("logs"):
    os.mkdir("logs")

lap_file_handler = logging.FileHandler("logs/lap-logger-{}.csv".format(today))
lap_logger = logging.getLogger("lap-logger")
lap_logger.addHandler(lap_file_handler)

gps_file_handler = logging.FileHandler("logs/gps-{}.csv".format(today))
gps_logger = logging.getLogger("gps-logger")
gps_logger.addHandler(gps_file_handler)
gps_logger.propagate = False

handler = RotatingFileHandler("logs/lemon-pi.log",
                              maxBytes=1000000,
                              backupCount=10)
handler.setFormatter(logging.Formatter(fmt='%(asctime)s.%(msecs)03d %(name)s %(levelname)s %(message)s', datefmt='%Y-%m-%d %H:%M:%S'))
handler.setLevel(logging.INFO)
logging.getLogger().addHandler(handler)
logging.getLogger().setLevel(logging.INFO)

logger.info("Lemon-Pi : starting up")

if not "SETTINGS_MODULE" in os.environ:
    os.environ["SETTINGS_MODULE"] = "lemon_pi.config.local_settings_car"

# main control thread
# responsibilities
#  0. disable wifi (to save battery) (or not)
#  1. launch UI
#  2. fire up OBD thread
#  3. fire up GPS thread
#  4. fire up Lora

gui = Gui(settings.DISPLAY_WIDTH, settings.DISPLAY_HEIGHT)

def init():
    try:
        # detect USB devices (should just be Lora)
        UsbDetector.init()

        # update tracks from web, if possible
        if not WifiManager.check_wifi_enabled():
            logger.info("enabling wifi")
            WifiManager.enable_wifi()

        TrackUpdater().update()

        # turn wifi off now, to save battery
        if settings.WIFI_DISABLED:
            WifiManager().disable_wifi()

        # enable sound generation
        Audio().start()
        StateMachine.init()
        MovementListener()

        maf_analyzer = MafAnalyzer(lap_logger)
        obd = ObdReader(maf_analyzer)
        gps = GpsReader()
        radio = Radio(settings.RADIO_DEVICE, settings.RADIO_KEY, ToCarMessage())
        meringue_comms = MeringueComms(settings.RADIO_DEVICE, settings.RADIO_KEY)
        radio_interface = RadioInterface(radio, meringue_comms, obd, None, maf_analyzer)

        # start a background thread to pull in gps data
        if settings.GPS_DISABLED:
            logger.warning("GPS has been disabled")
        else:
            gps.start()

        # start a background thread to pull in OBD data
        if settings.OBD_DISABLED:
            logger.warning("OBD has been disabled")
        else:
            obd.start()

        # start a background thread to manage the radio function
        if settings.RADIO_DISABLED:
            logger.warning("Radio has been disabled")
        else:
            radio.start()
        # and the radio interface maps car events to and from the radio
        radio_interface.start()

        logger.info("registering GUI providers")
        gui.register_speed_provider(gps)
        gui.register_time_provider(LocalTimeProvider())
        gui.register_temp_provider(obd)
        gui.register_fuel_provider(maf_analyzer)

        logger.info("reading tracks")
        tracks: [TrackLocation] = read_tracks()

        # show the main application
        gui.present_main_app()

        # bring in a button listener, to read the hardware button
        Button()

        logger.info("awaiting location to choose track")
        while not gps.is_working() or gps.get_lat_long() == (0, 0):
            time.sleep(1)
        closest_track = min(tracks, key=lambda x: haversine(gps.get_lat_long(), x.get_start_finish_target().midpoint))
        logger.info("closest track selected : {}".format(closest_track))
        # initialize the store that can read previous driving session
        # data from this track
        LapSessionStore.init(closest_track)
        lap_tracker = LapTracker(closest_track, maf_analyzer)
        gps.register_position_listener(lap_tracker)
        gui.register_lap_provider(lap_tracker)
        radio_interface.register_lap_provider(lap_tracker)
        radio.register_gps_provider(gps)
        meringue_comms.set_track_id(closest_track.code)
        if hasattr(settings, "MERINGUE_GRPC_OVERRIDE_URL"):
            meringue_comms.configure(settings.MERINGUE_GRPC_OVERRIDE_URL)
        else:
            meringue_comms.configure(None)
        # todo : if wifi is enabled, then create a wifi thingy and start it up
        # and register it with the radio_interface
        # radio interface ... on send, will see if it is set, and call it
    except Exception:
        logger.exception("exception in initialization")
        ExitApplicationEvent.emit()

Thread(target=init, daemon=True).start()

gui.display()
