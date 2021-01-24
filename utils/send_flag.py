
import os
import sys
import logging
import time
from python_settings import settings

from shared.generated.messages_pb2 import RaceStatus
from shared.radio import Radio
from shared.usb_detector import UsbDetector

logger = logging.getLogger(__name__)

logging.basicConfig(format='%(asctime)s %(name)s %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S',
                    level=logging.INFO)

if not "SETTINGS_MODULE" in os.environ:
    os.environ["SETTINGS_MODULE"] = "config.settings-pit"

if len(sys.argv) != 2:
    print("usage : {} [green|red|yellow|black]".format(__file__))
    sys.exit(1)

UsbDetector().init()

radio = Radio(settings.RADIO_DEVICE, settings.RADIO_KEY)
radio.start()

msg = RaceStatus()
msg.flagStatus = RaceStatus.RaceFlagStatus.Value(sys.argv[1].upper())

radio.send_async(msg)

logger.info("sleeping to give transmission enough time")
time.sleep(5)
logger.info("finished")