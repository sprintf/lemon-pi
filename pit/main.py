
import os
import logging
from logging.handlers import RotatingFileHandler
from python_settings import settings

from car.main import radio_interface
from pit.datasource.datasource1 import DataSource
from pit.datasource.datasource_handler import DataSourceHandler
from pit.leaderboard import RaceOrder
from shared.radio import Radio
from shared.usb_detector import UsbDetector

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
    os.environ["SETTINGS_MODULE"] = "config.settings-pit"


def run():
    # detect USB devices (should just be Lora)
    UsbDetector.init()

    # start the radio thread
    radio = Radio(settings.RADIO_DEVICE, settings.RADIO_KEY)
    radio_interface(radio)
    radio.start()

    # if we have a race specified
    if settings.RACE_ID > 0:
        # create a leaderboard
        leaderboard = RaceOrder()
        # filter race updates down to updates related to our car
        updater = DataSourceHandler(leaderboard, settings.TARGET_CAR)
        # start reading the race state
        ds = DataSource(settings.RACE_ID, updater)
        # and keep a thread going reading the race state
        if ds.connect():
            ds.start()


    # wait for incoming messages, and log them as they arrive
    while True:
        # pluck incoming messages off the queue
        item = radio.receive_queue.get()
        logger.info("received : {}".format(item.__repr__()))
        radio.receive_queue.task_done()


if __name__ == "__main__":
    logging.basicConfig(format='%(asctime)s %(name)s %(message)s',
                        datefmt='%Y-%m-%d %H:%M:%S',
                        level=logging.DEBUG)
    run()