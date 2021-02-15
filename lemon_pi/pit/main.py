
import os
import logging
from logging.handlers import RotatingFileHandler
from threading import Thread
from python_settings import settings

from lemon_pi.pit.radio_interface import RadioInterface
from lemon_pi.pit.datasource.datasource1 import DataSource
from lemon_pi.pit.datasource.datasource_handler import DataSourceHandler
from lemon_pi.pit.leaderboard import RaceOrder
from lemon_pi.shared.radio import Radio
from lemon_pi.shared.time_provider import LocalTimeProvider
from lemon_pi.shared.usb_detector import UsbDetector
from lemon_pi.pit.gui import Gui

logger = logging.getLogger(__name__)
if not os.path.isdir("logs"):
    os.mkdir("logs")

handler = RotatingFileHandler("logs/lemon-pit.log",
                              maxBytes=10000000,
                              backupCount=10)
handler.setFormatter(logging.Formatter(fmt='%(asctime)s %(name)s %(message)s', datefmt='%Y-%m-%d %H:%M:%S'))
handler.setLevel(logging.INFO)
logging.getLogger().addHandler(handler)
logging.getLogger().setLevel(logging.INFO)

logger.info("Lemon-Pit : starting up")


logging.basicConfig(format='%(asctime)s %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S',
                    level=logging.INFO)

if not "SETTINGS_MODULE" in os.environ:
    os.environ["SETTINGS_MODULE"] = "lemon_pi.config.local_settings_pit"


def run():
    gui = Gui()
    gui.register_time_provider(LocalTimeProvider())

    def init():
        gui.progress(10)
        # detect USB devices (should just be Lora)
        UsbDetector.init()
        gui.progress(40)

        # start the radio thread
        try:
            radio = Radio(settings.RADIO_DEVICE, settings.RADIO_KEY)
            RadioInterface(radio)
            radio.start()
            gui.progress(85)
        except KeyError:
            print("ERROR : Lora radio device not detected")
            gui.shutdown()

        # if we have a race specified
        if settings.RACE_ID != "":
            # create a leaderboard
            leaderboard = RaceOrder()
            # filter race updates down to updates related to our car
            updater = DataSourceHandler(leaderboard, settings.TARGET_CAR)
            # start reading the race state
            ds = DataSource(settings.RACE_ID, updater)
            # and keep a thread going reading the race state
            if ds.connect():
                ds.start()
            gui.progress(90)
        gui.progress(100)

    Thread(target=init, daemon=True).start()
    gui.display()

if __name__ == "__main__":
    logging.basicConfig(format='%(asctime)s %(name)s %(message)s',
                        datefmt='%Y-%m-%d %H:%M:%S',
                        level=logging.DEBUG)
    run()