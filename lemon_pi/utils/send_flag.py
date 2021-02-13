
import os
import sys
import logging
import time
from python_settings import settings

from lemon_pi.shared.generated.messages_pb2 import (
    RaceStatus,
    RaceFlagStatus
)
from lemon_pi.shared.radio import Radio
from lemon_pi.shared.usb_detector import UsbDetector

logger = logging.getLogger(__name__)

logging.basicConfig(format='%(asctime)s %(name)s %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S',
                    level=logging.INFO)

if not "SETTINGS_MODULE" in os.environ:
    os.environ["SETTINGS_MODULE"] = "lemon_pi.config.local_settings_pit"

if len(sys.argv) != 2:
    print("usage : {} [green|red|yellow|black]".format(__file__))
    sys.exit(1)

UsbDetector().init()

radio = Radio(settings.RADIO_DEVICE, settings.RADIO_KEY)
radio.start()

msg = RaceStatus()
msg.flag_status = RaceFlagStatus.Value(sys.argv[1].upper())

radio.send_async(msg)

logger.info("sleeping to give transmission enough time")
time.sleep(5)
logger.info("finished")