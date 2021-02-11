
import os
import sys
import logging
import time
from python_settings import settings

from lemon_pi.shared.generated.messages_pb2 import RacePosition
from lemon_pi.shared.radio import Radio
from lemon_pi.shared.usb_detector import UsbDetector

logger = logging.getLogger(__name__)

logging.basicConfig(format='%(asctime)s %(name)s %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S',
                    level=logging.INFO)

if not "SETTINGS_MODULE" in os.environ:
    os.environ["SETTINGS_MODULE"] = "lemon_pi.config.local_settings_pit"

if len(sys.argv) != 3:
    print("usage : {} [car-number] [1-3]".format(__file__))
    print("  e.g. {} 181 2".format(__file__))
    sys.exit(1)

car_number = sys.argv[1]
choice = int(sys.argv[2])

def build_message(choice):
    msg = RacePosition()
    if choice == 1:
        msg.car_number = car_number
        msg.position = 1
        msg.lap_count = 12
    if choice == 2:
        msg.car_number = car_number
        msg.position = 2
        msg.lap_count = 13
        msg.car_ahead.car_number = "9"
        msg.car_ahead.gap_text = "1:15s"
    if choice == 3:
        msg.car_number = "55"
        msg.position = 3
        msg.lap_count = 13
        msg.car_ahead.car_number = car_number
        msg.car_ahead.gap_text = "5s"
    else:
        Exception("not a valid choice")
    return msg


UsbDetector().init()

radio = Radio(settings.RADIO_DEVICE, settings.RADIO_KEY)
radio.start()
radio.send_async(build_message(choice))

logger.info("sleeping to give transmission enough time")
time.sleep(5)
logger.info("finished")

