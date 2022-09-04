
import os
import logging
import time
from logging.handlers import RotatingFileHandler
from threading import Thread
from python_settings import settings

from lemon_pi.pit.meringue_comms_pit import MeringueCommsPitsReader
from lemon_pi.pit.radio_interface import RadioInterface
from lemon_pi_pb2 import ToPitMessage
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

if "SETTINGS_MODULE" not in os.environ:
    os.environ["SETTINGS_MODULE"] = "lemon_pi.config.local_settings_pit"


def run():
    gui = Gui(settings.TARGET_CARS)
    gui.register_time_provider(LocalTimeProvider())

    def init():
        gui.progress(10)
        # detect USB devices (should just be Lora)
        UsbDetector.init()
        gui.progress(40)

        # start the radio thread
        try:
            radio = Radio(settings.RADIO_DEVICE, settings.RADIO_KEY, ToPitMessage())
            meringue_comms = MeringueCommsPitsReader(settings.RADIO_DEVICE, settings.TARGET_CARS, settings.RADIO_KEY)
            RadioInterface(radio, meringue_comms).start()
            radio.start()

            meringue_comms.set_track_id(settings.TRACK_CODE)
            if hasattr(settings, "MERINGUE_GRPC_OVERRIDE_URL"):
                meringue_comms.configure(settings.MERINGUE_GRPC_OVERRIDE_URL)
            else:
                meringue_comms.configure(None)

            # this launches a series of threads, so we do not actually call start() on it
            meringue_comms.run()
            time.sleep(2)
            gui.progress(85)
        except KeyError:
            print("ERROR : Lora radio device not detected")
            gui.shutdown()

        gui.progress(100)

    Thread(target=init, daemon=True).start()
    gui.display()


if __name__ == "__main__":
    logging.basicConfig(format='%(asctime)s %(name)s %(message)s',
                        datefmt='%Y-%m-%d %H:%M:%S',
                        level=logging.INFO)
    run()
