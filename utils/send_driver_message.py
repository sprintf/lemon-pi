
import os
import logging
import time
from python_settings import settings

from shared.generated.messages_pb2 import DriverMessage
from shared.radio import Radio
from shared.usb_detector import UsbDetector

logger = logging.getLogger(__name__)

logging.basicConfig(format='%(asctime)s %(name)s %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S',
                    level=logging.INFO)

if not "SETTINGS_MODULE" in os.environ:
    os.environ["SETTINGS_MODULE"] = "config.local_settings_pit"

UsbDetector().init()

radio = Radio(settings.RADIO_DEVICE, settings.RADIO_KEY)
radio.start()

msg = DriverMessage()
msg.text = "Get yer arse into gear!"

radio.send_async(msg)

logger.info("sleeping to give transmission enough time")
time.sleep(5)
logger.info("finished")